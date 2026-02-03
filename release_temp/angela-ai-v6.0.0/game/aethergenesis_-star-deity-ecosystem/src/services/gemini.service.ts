import { Injectable } from '@angular/core';
import { GoogleGenAI } from "@google/genai";
import { environment } from "../environments/environment";

// In a real app, this would be in a separate, git-ignored file.
// For this applet, we assume `process.env.API_KEY` is available.
// We are adding a fallback for local dev if needed.
const API_KEY = process.env.API_KEY || environment.apiKey;

@Injectable({ providedIn: 'root' })
export class GeminiService {
  private ai: GoogleGenAI | null = null;

  constructor() {
    if (!API_KEY) {
      console.warn("API_KEY for Gemini is not set. Service will be disabled.");
    } else {
      this.ai = new GoogleGenAI({ apiKey: API_KEY });
    }
  }

  async generateGameEvent(currentStateDescription: string): Promise<string | null> {
    if (!this.ai) {
      return Promise.resolve("A minor seismic tremor was recorded. Geothermal activity appears stable. [Gemini Disabled]");
    }
    
    const model = 'gemini-2.5-flash';
    const prompt = `Based on the following game state, generate a single, concise, flavorful event description (max 2 sentences) for a sci-fi planet simulation game. The tone should be slightly mysterious and grand. Do not use markdown or formatting.
    
    Game State:
    ${currentStateDescription}
    
    Event Description:`;

    try {
      const response = await this.ai.models.generateContent({
        model: model,
        contents: prompt,
        config: {
            systemInstruction: "You are the 'World-Mind' of a sci-fi game called AetherGenesis. You provide narrative flavor text for game events.",
            temperature: 0.9,
            topK: 10,
            topP: 0.9,
        }
      });
      return response.text.trim();
    } catch (error) {
      console.error("Error generating content with Gemini:", error);
      throw new Error("Failed to generate game event from AI.");
    }
  }
}
