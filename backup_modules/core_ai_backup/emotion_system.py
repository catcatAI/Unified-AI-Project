"""
Emotion System for the AI
This module manages the AI's emotional state and responses.
"""

class EmotionSystem:
    """System for managing AI emotions and emotional responses"""
    
    def __init__(self, personality_profile: dict = None, config: dict = None) -> None:
        self.personality = personality_profile or 
        self.config = config or 
        
        # Default emotion from personality, or overall default
        default_tone = "neutral"
        if self.personality:
            default_tone = self.personality.get("communication_style", ).get("default_tone", "neutral")
        
        self.current_emotion = default_tone
        
        # Simple internal emotion map for text endings
        self.emotion_expressions = self.config.get("emotion_map", {
            "neutral": {"text_ending": ""},  # Neutral has no specific ending
            "empathetic": {"text_ending": " (gently)"},
            "playful": {"text_ending": " (playfully) ✨"},
            "sad_response": {"text_ending": " (with a sigh)"}  # AI expressing sadness
        })
        
        print(f"EmotionSystem initialized. Default emotion: {self.current_emotion}")
    
    def update_emotion_based_on_input(self, input_data: dict, context: dict = None) -> str:
        """
        Analyzes input and context to update the AI's emotional state.
        Returns the new emotion.
        """
        text_input = input_data.get("text", "").lower
        new_emotion = self.current_emotion  # Default to current if no change
        
        # Simple keyword-based emotion detection
        if any(keyword in text_input for keyword in ["sad", "unhappy", "depressed", "crying"]):
            new_emotion = "empathetic"
        elif any(keyword in text_input for keyword in ["happy", "great", "yay", "awesome", "wonderful", "fantastic"]):
            new_emotion = "playful"
        # Add more rules as needed, e.g., for anger, fear, etc.
        # Could also reset to neutral after some interactions or based on context.
        else:
            # Optionally, decay to neutral if no strong cues, or maintain current.
            # For now, if no strong cue, keep current or revert to personality default.
            default_personality_tone = "neutral"
            if self.personality:
                default_personality_tone = self.personality.get("communication_style", ).get("default_tone", "neutral")
            new_emotion = default_personality_tone  # Revert to default if no specific trigger
        
        if new_emotion != self.current_emotion:
            print(f"EmotionSystem: Emotion changing from '{self.current_emotion}' to '{new_emotion}' based on input: '{text_input[:30]}...'")
            self.current_emotion = new_emotion
        
        return self.current_emotion
    
    def get_current_emotion_expression(self) -> dict:
        """
        Returns cues for expressing the current emotion, primarily a text_ending.
        """
        expression = self.emotion_expressions.get(self.current_emotion)
        if expression:
            return expression
        else:
            # Fallback to neutral if current_emotion isn't in the map
            return self.emotion_expressions.get("neutral", {"text_ending": ""})

if __name__ == "__main__":
    # Example usage
    example_personality = {
        "profile_name": "miko_base",
        "communication_style": {"default_tone": "neutral"},
        # ... other personality data
    }
    
    emotion_sys = EmotionSystem(personality_profile=example_personality)
    print(f"Initial emotion expression: {emotion_sys.get_current_emotion_expression}")
    
    sample_input = {"text": "I am feeling a bit sad today."}
    emotion_sys.update_emotion_based_on_input(sample_input)
    print(f"Emotion expression after input: {emotion_sys.get_current_emotion_expression}")