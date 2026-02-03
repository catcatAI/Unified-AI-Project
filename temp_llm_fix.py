    async def _generate_llm_response(self, thought: Dict[str, Any]) -> str:
        """使用LLM生成响应 - 修复版本"""
        if not self.llm_available or not self.available_models:
            logger.info("LLM not available, using rule-based response")
            return self._generate_rule_based_response(thought)
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(thought)
            if cache_key in self.response_cache:
                logger.info("Using cached response")
                return self.response_cache[cache_key]
            
            # 构建简化的提示
            user_input = thought.get("user_input", "")
            strategy = thought.get("strategy", "general")
            
            # 使用更简单有效的提示
            if strategy == "greeting":
                prompt = f"User: {user_input}\nYou are a helpful AI assistant. Respond warmly and briefly:"
            elif strategy == "question_answering":
                prompt = f"User: {user_input}\nYou are a helpful AI assistant. Provide a clear, concise answer:"
            else:
                prompt = f"User: {user_input}\nYou are a helpful AI assistant. Respond naturally:"
            
            # 使用最快的模型
            model = self._select_fast_model()
            
            # 调用Ollama API - 增加超时和重试
            logger.info(f"Attempting LLM generation with model: {model}")
            
            for attempt in range(3):  # 最多重试3次
                try:
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,  # 适度的随机性
                                "num_predict": 100,  # 限制长度但不要太短
                                "top_k": 20,
                                "top_p": 0.9,
                                "repeat_penalty": 1.1
                            }
                        },
                        timeout=15  # 增加超时时间
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        llm_response = result.get("response", "").strip()
                        
                        if llm_response and len(llm_response) > 5:
                            # 缓存成功的响应
                            if len(self.response_cache) < self.max_cache_size:
                                self.response_cache[cache_key] = llm_response
                            
                            logger.info(f"LLM response generated successfully: {llm_response[:50]}...")
                            return llm_response
                        else:
                            logger.warning(f"LLM response too short or empty: '{llm_response}'")
                    else:
                        logger.warning(f"LLM HTTP error: {response.status_code}")
                
                except requests.exceptions.Timeout:
                    logger.warning(f"LLM timeout on attempt {attempt + 1}")
                    continue
                except Exception as e:
                    logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                    continue
            
            logger.warning("All LLM attempts failed, using rule-based response")
            
        except Exception as e:
            logger.error(f"LLM generation completely failed: {e}")
        
        # 回退到基于规则的响应
        return self._generate_rule_based_response(thought)