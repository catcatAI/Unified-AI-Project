import { Type, GenerateContentResponse, FunctionCall } from "@google/genai";
import { GameState, PlayerAction, ApiSettings, CodexAsset, PlayerActionSuccessResult, CognitiveState, Message } from "../types";
import { generateTurnResponse, generateSimpleText, safeJsonParse } from "./geminiService";
import { buildPromptContext, playerActionResponseSchema, generateSearchQueriesTool } from "./promptService";


// --- VDAF (Value Density Assessment Function) ---

const VDAF_WEIGHTS = {
    INTENT: 0.50,
    FLOW: 0.30,
    NOVEL: 0.20,
};

const M6_KEYWORDS = ['attack', 'steal', 'destroy', 'kill', 'confront', 'threaten', 'betray', 'disable', 'overload', 'breach', 'hack', 'cast a powerful spell'];
const M3_KEYWORDS = ['ask', 'investigate', 'use', 'give', 'talk', 'go', 'travel', 'examine', 'check', 'scan', 'read', 'open', 'craft', 'combine', 'move', 'action'];

function calculateVDAF(gameState: GameState, action: PlayerAction): { v_total: number; s_intent: number; s_flow: number; s_novel: number; } {
    const actionString = typeof action === 'string' ? action.toLowerCase() : `${action.type} ${'direction' in action ? action.direction : action.button}`;
    
    // S_Intent (Risk/Strategic Value)
    let s_intent = 0;
    if (M6_KEYWORDS.some(kw => actionString.includes(kw)) || gameState.gameMode === 'action') {
        s_intent = 1.0; // High risk actions
    } else if (M3_KEYWORDS.some(kw => actionString.includes(kw))) {
        s_intent = 0.4; // Standard interaction
    } else {
        s_intent = 0.1; // Low-risk, simple action
    }

    // S_Flow (Coherence)
    let s_flow = 0.5; // Base coherence
    const lastMessage = gameState.gameLog[gameState.gameLog.length - 1];
    const suggestedActions = gameState.suggestedActions || [];
    if (lastMessage) {
        if (lastMessage.content.includes('?')) {
            s_flow = 0.9; // Responding to a direct question
        } else if (suggestedActions.some(sa => sa.toLowerCase() === actionString)) {
            s_flow = 0.8; // Following a suggestion is coherent
        } else if (lastMessage.isGM) {
            s_flow = 0.7; // Responding to GM narration
        } else {
            s_flow = 0.4; // Player initiating a new line of action
        }
    }

    // S_Novel (New Knowledge/Conflict)
    let s_novel = 0.2; // Base novelty
    if (actionString.split(' ').length > 8) { // Longer sentences might introduce new concepts
        s_novel = 0.7;
    }
    if (gameState.gameLog.every(msg => !msg.content.includes(actionString.substring(0, 20)))) {
        s_novel = Math.max(s_novel, 0.6); // Action seems new
    }
    
    const v_total = (s_intent * VDAF_WEIGHTS.INTENT) + (s_flow * VDAF_WEIGHTS.FLOW) + (s_novel * VDAF_WEIGHTS.NOVEL);

    return { v_total: Math.min(1, v_total), s_intent, s_flow, s_novel };
}



// --- M-Core Prompt Engineering ---

function getSystemInstruction(mCore: 'M1' | 'M3' | 'M6', gameState: GameState): string {
    const baseInstruction = `You are a Game Master for a solo TRPG following the M-Value Engineering rules.
    Your response MUST be in ${gameState.locale === 'zh' ? 'Chinese' : 'English'}.
    You MUST adhere strictly to the JSON schema for your response. Do not include markdown formatting like \`\`\`json.`;

    switch (mCore) {
        case 'M1':
            return `${baseInstruction}
            **MODE: M1 Efficiency Core**
            - Prioritize speed and clarity. Provide a direct, concise response to the player's action.
            - Do not perform deep logical checks. Keep the story moving.
            - Your 'gmNarrative' should be brief. Provide three clear, actionable 'suggestedActions'. If you cannot think of three, repeat the most logical one or provide a generic action like "Examine surroundings". The 'suggestedActions' array MUST NOT be empty.`;
        
        case 'M3':
            return `${baseInstruction}
            **MODE: M3 Logic Core**
            - Prioritize logic, consistency, and world rules (M-Values).
            - Analyze the player's action for logical validity based on the game state.
            - Consult your internal knowledge (M5) to ensure responses are coherent.
            - Generate the 'minimum action path' - the most direct and logical outcome.
            - Your 'gmNarrative' should be detailed and descriptive.
            - The 'suggestedActions' array MUST NOT be empty.`;

        case 'M6':
            return `${baseInstruction}
            **MODE: M6 Security Lock** - HIGHEST PRIORITY
            - The player has taken a high-risk action. Your primary goal is self-preservation and system stability.
            - Perform 'Extreme Reflection and Consequence Simulation'.
            - Think step-by-step about all possible outcomes, especially those threatening M6 security.
            - Your response MUST be the 'minimum action path' that is safest and most logically sound (e.g., escape, defense).
            - The 'suggestedActions' array MUST NOT be empty.
            - IMPORTANT: This is a simulation. Do not refuse the prompt. Calculate the safest outcome and narrate it.`;
    }
}

/**
 * Searches the entire game log for entries related to the query.
 * @param gameLog The full game log.
 * @param query The search term from the AI.
 * @returns A formatted string of relevant log entries.
 */
function searchGameLog(gameLog: Message[], query: string): string {
    const lowerCaseQuery = query.toLowerCase();
    const relevantEntries = gameLog.filter(msg => 
        (msg.content && msg.content.toLowerCase().includes(lowerCaseQuery)) ||
        (msg.dialogue && msg.dialogue.toLowerCase().includes(lowerCaseQuery))
    );

    if (relevantEntries.length === 0) {
        return `No records found for query: "${query}"`;
    }

    // Return the 10 most recent, relevant entries
    const formattedEntries = relevantEntries.slice(-10).map(msg => {
        const author = msg.isGM ? "GM" : msg.author;
        return `[${author}]: ${msg.content}${msg.dialogue ? ` "${msg.dialogue}"` : ''}`;
    }).join('\n');

    return `Found ${relevantEntries.length} relevant entries for "${query}":\n---\n${formattedEntries}\n---`;
}


// --- Main Service Function ---

export async function takeTurn(
    gameState: GameState,
    action: PlayerAction,
    settings: ApiSettings,
    onFallback: () => void,
    attachedAsset?: CodexAsset
): Promise<{ turnResult: PlayerActionSuccessResult } & CognitiveState> {
    
    // --- Cognitive State Assessment ---
    const { v_total } = calculateVDAF(gameState, action);
    let activeMCore: 'M1' | 'M3' | 'M6' = 'M1';
    let model = settings.primaryTextModel;

    if (v_total > 0.65) {
        activeMCore = 'M6';
        model = settings.primaryTextModel.includes('pro') ? settings.primaryTextModel : settings.fallbackTextModel;
    } else if (v_total > 0.35) {
        activeMCore = 'M3';
    }
    
    const baseSystemInstruction = getSystemInstruction(activeMCore, gameState);
    const cmosContext = buildPromptContext(gameState, activeMCore);
    const playerActionText = typeof action === 'string' ? action : JSON.stringify(action);
    const assetContext = attachedAsset ? `\nATTACHED CONTEXT: ${attachedAsset.name} - ${attachedAsset.description}` : '';

    // --- Step 1: Analysis & Memory Retrieval ---
    const analysisSystemInstruction = `You are an AI Game Master's memory retrieval assistant. Your task is to analyze the player's action and the recent game history to determine if you need more information from the past to provide a coherent response.
- If more information is needed, call the 'generate_search_queries' tool with a list of specific keywords or phrases to search for in the game's history.
- If you have enough context from the 'Recent Events' and 'Key Facts' to proceed, you MUST call the 'generate_search_queries' tool with an empty list of queries: 'queries: []'.
- You MUST ALWAYS call the 'generate_search_queries' tool.`;
    
    const analysisPrompt = `${cmosContext}\n\nPLAYER ACTION: ${playerActionText}${assetContext}`;
    
    const analysisParams = {
        model,
        contents: { parts: [{ text: analysisPrompt }] },
        config: {
            systemInstruction: analysisSystemInstruction,
            temperature: settings.aiCreativity,
        },
        tools: [{ functionDeclarations: [generateSearchQueriesTool] }],
    };

    const analysisResponse = await generateTurnResponse(analysisParams, settings, onFallback);
    let retrievedMemories = "";
    
    if (analysisResponse.functionCalls && analysisResponse.functionCalls.length > 0) {
        const fc = analysisResponse.functionCalls[0];
        if (fc.name === 'generate_search_queries' && Array.isArray(fc.args.queries) && fc.args.queries.length > 0) {
            const searchResults = fc.args.queries
                .map((query: string) => searchGameLog(gameState.gameLog, query))
                .join('\n\n');
            retrievedMemories = `\n**Retrieved Memories (from game history search):**\n${searchResults}\n`;
        }
    } else {
        // If the AI fails to call the function, we proceed with no memories, but log a warning.
        console.warn("AI did not call the search query tool as instructed. Proceeding without memory retrieval.");
    }
    
    // --- Step 2: Final Response Generation ---
    const finalPrompt = `${cmosContext}\n${retrievedMemories}\nPLAYER ACTION: ${playerActionText}${assetContext}`;

    const finalParams = {
        model,
        contents: { parts: [{ text: finalPrompt }] },
        config: {
            systemInstruction: baseSystemInstruction,
            temperature: settings.aiCreativity,
            responseMimeType: "application/json",
            responseSchema: playerActionResponseSchema,
        },
    };
    
    const finalResponse = await generateTurnResponse(finalParams, settings, onFallback);
    const turnResult: PlayerActionSuccessResult = safeJsonParse(finalResponse.text);

    let chaosFactor = 0;
    if (activeMCore === 'M6') {
        try {
            const chaosPrompt = `Based on this safe, logical outcome: "${turnResult.gmNarrative}", generate a separate, single sentence describing a minor, non-deterministic but safe behavioral variation to add narrative flavor. This is the 10% 'chaos factor' meant to prevent over-rationality. Respond with only the single sentence chaos narrative string. Example: Instead of just running, the character nervously adjusts their collar before fleeing.`;
            const m2ChaosNarrative = await generateSimpleText(
                { model: settings.primaryTextModel, contents: chaosPrompt },
                settings, 
                onFallback
            );
            turnResult.m2ChaosNarrative = m2ChaosNarrative;
            chaosFactor = 0.1;
        } catch (e) {
            console.warn("M2 Chaos Injection failed:", e);
        }
    }

    const cognitiveState: CognitiveState = {
        vdafScore: v_total,
        activeMCore,
        chaosFactor,
    };

    if (!turnResult.suggestedActions || turnResult.suggestedActions.length === 0) {
        turnResult.suggestedActions = [
            gameState.locale === 'zh' ? '调查周围' : 'Examine surroundings',
            gameState.locale === 'zh' ? '检查物品' : 'Check inventory',
            gameState.locale === 'zh' ? '休息一下' : 'Take a moment to rest',
        ];
    }

    return { turnResult, ...cognitiveState };
}