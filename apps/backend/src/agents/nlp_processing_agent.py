import asyncio
import uuid
import json
import logging
import re
from typing import Dict, Any, List
from collections import Counter

from .base_agent import BaseAgent
from hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class NLPProcessingAgent(BaseAgent):
    """
    A specialized agent for natural language processing tasks like text summarization,
    sentiment analysis, entity extraction, and language translation.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_text_summarization_v1.0",
                "name": "text_summarization",
                "description": "Generates concise summaries of provided text content.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content to summarize"},
                    {"name": "summary_length", "type": "string", "required": False, "description": "Desired summary length (short, medium, long)"}
                ],
                "returns": {"type": "object", "description": "Summarized text and metadata."}
            },
            {
                "capability_id": f"{agent_id}_sentiment_analysis_v1.0",
                "name": "sentiment_analysis",
                "description": "Performs sentiment analysis on text content.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}
                ],
                "returns": {"type": "object", "description": "Sentiment analysis results including polarity and emotions."}
            },
            {
                "capability_id": f"{agent_id}_entity_extraction_v1.0",
                "name": "entity_extraction",
                "description": "Extracts named entities (people, organizations, locations, etc.) from text.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}
                ],
                "returns": {"type": "object", "description": "Extracted entities categorized by type."}
            },
            {
                "capability_id": f"{agent_id}_language_detection_v1.0",
                "name": "language_detection",
                "description": "Detects the language of provided text content.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}
                ],
                "returns": {"type": "object", "description": "Detected language and confidence score."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logging.info(f"[{self.agent_id}] NLPProcessingAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "text_summarization" in capability_id:
                result = self._generate_text_summary(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "sentiment_analysis" in capability_id:
                result = self._perform_sentiment_analysis(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "entity_extraction" in capability_id:
                result = self._extract_entities(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "language_detection" in capability_id:
                result = self._detect_language(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    def _generate_text_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a summary of the provided text."""
        text = params.get('text', '')
        summary_length = params.get('summary_length', 'medium')
        
        if not text:
            raise ValueError("No text provided for summarization")
        
        # Simple extractive summarization based on sentence scoring
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"summary": "", "original_length": len(text), "summary_length": 0}
        
        # Calculate word frequencies
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)
        
        # Score sentences based on word frequency
        sentence_scores = []
        for sentence in sentences:
            sentence_words = re.findall(r'\b\w+\b', sentence.lower())
            score = sum(word_freq[word] for word in sentence_words)
            sentence_scores.append((sentence, score))
        
        # Sort sentences by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Determine number of sentences for summary
        if summary_length == 'short':
            num_sentences = max(1, len(sentences) // 4)
        elif summary_length == 'long':
            num_sentences = max(1, len(sentences) // 2)
        else:  # medium
            num_sentences = max(1, len(sentences) // 3)
        
        # Select top sentences
        top_sentences = sentence_scores[:num_sentences]
        # Sort by original order
        top_sentences.sort(key=lambda x: sentences.index(x[0]))
        summary = '. '.join([s[0] for s in top_sentences]) + '.'
        
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(text),
            "num_sentences_original": len(sentences),
            "num_sentences_summary": len(top_sentences)
        }

    def _perform_sentiment_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Performs sentiment analysis on text."""
        text = params.get('text', '')
        
        if not text:
            raise ValueError("No text provided for sentiment analysis")
        
        # Simple sentiment analysis using keyword matching
        # In a real implementation, this would use a proper NLP model
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'brilliant', 'outstanding',
            'perfect', 'superb', 'marvelous', 'terrific', 'fabulous', 'incredible', 'awesome', 'delightful',
            'pleasant', 'enjoyable', 'satisfactory', 'fine', 'nice', 'positive', 'happy', 'pleased',
            'glad', 'cheerful', 'joyful', 'enthusiastic', 'optimistic', 'confident', 'hopeful', 'encouraging'
        }
        
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'dreadful', 'abysmal', 'atrocious', 'appalling',
            'disgusting', 'revolting', 'nauseating', 'sickening', 'vile', 'ghastly', 'grim', 'dismal',
            'poor', 'mediocre', 'inferior', 'substandard', 'unsatisfactory', 'disappointing', 'frustrating',
            'annoying', 'irritating', 'bothersome', 'troublesome', 'problematic', 'difficult', 'challenging',
            'negative', 'sad', 'unhappy', 'depressed', 'displeased', 'upset', 'angry', 'furious',
            'outraged', 'livid', 'enraged', 'incensed', 'irate', 'infuriated', 'offended', 'hurt'
        }
        
        neutral_words = {
            'okay', 'alright', 'fine', 'acceptable', 'adequate', 'sufficient', 'moderate', 'average',
            'normal', 'standard', 'regular', 'usual', 'typical', 'common', 'ordinary', 'conventional',
            'expected', 'predictable', 'stable', 'consistent', 'reliable', 'steady', 'unchanged'
        }
        
        # Tokenize and normalize text
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Count sentiment words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        neutral_count = sum(1 for word in words if word in neutral_words)
        
        # Calculate sentiment scores
        total_sentiment_words = positive_count + negative_count + neutral_count
        if total_sentiment_words == 0:
            # If no sentiment words found, assume neutral
            polarity = 0.0
            confidence = 0.5
        else:
            polarity = (positive_count - negative_count) / total_sentiment_words
            confidence = total_sentiment_words / len(words)
        
        # Determine overall sentiment
        if polarity > 0.1:
            overall_sentiment = "positive"
        elif polarity < -0.1:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        return {
            "overall_sentiment": overall_sentiment,
            "polarity_score": round(polarity, 3),
            "confidence": round(confidence, 3),
            "positive_words_count": positive_count,
            "negative_words_count": negative_count,
            "neutral_words_count": neutral_count,
            "total_words": len(words),
            "sentiment_words_ratio": round(total_sentiment_words / len(words), 3) if len(words) > 0 else 0
        }

    def _extract_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts named entities from text."""
        text = params.get('text', '')
        
        if not text:
            raise ValueError("No text provided for entity extraction")
        
        # Simple entity extraction using pattern matching
        # In a real implementation, this would use a proper NER model
        
        # Extract potential person names (capitalized words)
        person_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        persons = re.findall(person_pattern, text)
        persons = [p for p in persons if len(p) > 1 and p.lower() not in {'The', 'This', 'That', 'These', 'Those'}]
        
        # Extract potential organizations (all caps or capitalized phrases)
        org_pattern = r'\b(?:[A-Z]{2,}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        organizations = re.findall(org_pattern, text)
        organizations = [o for o in organizations if len(o) > 2 and o not in persons]
        
        # Extract potential locations (capitalized words that might be locations)
        location_keywords = {'street', 'avenue', 'road', 'boulevard', 'drive', 'lane', 'place', 'square', 'plaza',
                           'city', 'town', 'village', 'county', 'state', 'province', 'country', 'nation', 'region',
                           'district', 'borough', 'municipality', 'capital', 'metropolis', 'suburb', 'neighborhood'}
        location_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Street|Ave|Road|Rd|Blvd|Dr|Ln|Pl|Sq|Plaza|City|Town|Village|County|State|Province|Country|Region|District|Borough|Municipality|Capital|Metropolis|Suburb|Neighborhood))?\b'
        locations = re.findall(location_pattern, text)
        locations = [l for l in locations if len(l) > 2]
        
        # Extract potential dates
        date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b'
        dates = re.findall(date_pattern, text)
        
        # Extract potential emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Extract potential phone numbers
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phones = re.findall(phone_pattern, text)
        
        return {
            "persons": list(set(persons)),  # Remove duplicates
            "organizations": list(set(organizations)),
            "locations": list(set(locations)),
            "dates": list(set(dates)),
            "emails": list(set(emails)),
            "phones": list(set(phones)),
            "total_entities": len(set(persons)) + len(set(organizations)) + len(set(locations)) + len(set(dates)) + len(set(emails)) + len(set(phones))
        }

    def _detect_language(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detects the language of text."""
        text = params.get('text', '')
        
        if not text:
            raise ValueError("No text provided for language detection")
        
        # Simple language detection based on character sets and common words
        # In a real implementation, this would use a proper language detection library
        
        # Character set detection
        latin_chars = len(re.findall(r'[A-Za-z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        arabic_chars = len(re.findall(r'[\u0600-\u06ff]', text))
        cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', text))
        
        total_chars = len(text)
        
        if total_chars == 0:
            return {"language": "unknown", "confidence": 0.0}
        
        # Language detection based on character sets
        char_scores = {
            "English": latin_chars / total_chars if latin_chars > 0 else 0,
            "Chinese": chinese_chars / total_chars if chinese_chars > 0 else 0,
            "Arabic": arabic_chars / total_chars if arabic_chars > 0 else 0,
            "Russian": cyrillic_chars / total_chars if cyrillic_chars > 0 else 0
        }
        
        # Find the language with the highest score
        detected_language = max(char_scores, key=char_scores.get)
        confidence = char_scores[detected_language]
        
        # If confidence is low, check for common English words
        if confidence < 0.3:
            common_english_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'}
            words = re.findall(r'\b\w+\b', text.lower())
            english_word_count = sum(1 for word in words if word in common_english_words)
            if len(words) > 0 and english_word_count / len(words) > 0.2:
                detected_language = "English"
                confidence = english_word_count / len(words)
        
        return {
            "language": detected_language,
            "confidence": round(confidence, 3),
            "character_analysis": {
                "latin": latin_chars,
                "chinese": chinese_chars,
                "arabic": arabic_chars,
                "cyrillic": cyrillic_chars,
                "total": total_chars
            }
        }

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )


if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:nlp_processing_agent_{uuid.uuid4().hex[:6]}"
        agent = NLPProcessingAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nNLPProcessingAgent manually stopped.")