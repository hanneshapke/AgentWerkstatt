# AgentWerkstatt Roadmap

This roadmap outlines the planned features and improvements for AgentWerkstatt, a minimalistic agentic framework.

## 🚀 v0.2.0 - Foundation Improvements

### Core Framework
- [x] **Configuration Validation**: Schema validation for config.yaml
- [x] **Memory Management**: Basic memory and context management using mem0.
- [x] **Self-Reflection**: Agent self-evaluation and improvement
- [x] **Planning & Reasoning**: Multi-step task planning

### LLM Providers
- [x] **OpenAI Integration**: GPT-OSS support
- [x] **Local LLMs**: Ollama and LMStudio support
- [ ] **Google AI**: Gemini Pro integration
- [ ] **LLM Router**: Automatic model selection based on task complexity

### 3rd Party Integrations
- [x] **Tavily**: Web search
- [x] **Memory Provider**: Find a memory provider and integrate it in Docker setup
- [x] **Agent Observability**: Find a way to observe agent behavior and performance

### Bug Fixes
- [ ] **MyPy Compliance**: Fix all type checking issues
- [ ] **Edge Cases**: Handle API rate limiting and network failures gracefully

## 🔧 v0.3.0 - Developer Experience

### Developer Experience
- [ ] **Type Safety**: Complete type annotations throughout codebase
- [ ] **Documentation**: Comprehensive API documentation and examples
- [ ] **Testing**: Increase test coverage to >90%
- [ ] **Performance Profiling**: Basic performance monitoring and optimization

### Examples
- [ ] **Tool discovers an API and uses it to get information**: Automatically discover an API and use it to get information to generate tools.

### Advanced Features
- [ ] **Learning from Feedback**: Incorporate user feedback into responses
- [ ] **RL Example**: Use RL to learn from feedback


## 🤝 Contributing

We welcome contributions! Check our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs and feature requests
- Submitting pull requests
- Code style and testing requirements
- Community guidelines


---

*This roadmap is subject to change based on community feedback, market needs, and technical discoveries. We prioritize shipping value early and often while maintaining high quality standards.*
