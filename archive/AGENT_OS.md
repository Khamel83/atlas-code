# Agent OS Integration

Atlas Code V2 integrates with Agent OS for development standards and workflow management.

## Agent OS Repository
**🔗 Source:** https://github.com/Khamel83/agent-os

Agent OS provides:
- Development standards and coding guidelines
- Project-specific instructions and workflows  
- Template structures for consistent development
- Automated development process documentation

## Usage in Atlas Code

### Automatic Integration
Atlas Code automatically looks for an `agent_os/` directory in your project and:
- Loads coding standards from `agent_os/standards/`
- Applies relevant instructions from `agent_os/instructions/`
- Enhances prompts with project-specific context
- Maintains consistency across development sessions

### Initialize Agent OS
```bash
./atlas-code --init-agent-os
```

This creates:
```
agent_os/
├── standards/
│   └── python.md          # Sample Python coding standards
├── instructions/
│   └── testing.md         # Sample testing instructions
├── commands/              # Custom development commands
├── templates/             # Project templates
└── project_info.json     # Project metadata
```

### Customization
Edit files in `agent_os/` to customize for your project:
- Add language-specific standards
- Define testing and deployment procedures
- Set up project-specific workflows
- Configure development best practices

### Integration Benefits
- **Consistent Code Quality**: All AI coding follows your standards
- **Project Context**: AI understands your specific requirements
- **Workflow Automation**: Standard procedures applied automatically
- **Team Alignment**: Shared standards across all development

## Agent OS vs Atlas Code V2
- **Agent OS**: Development standards and workflow framework
- **Ralex**: AI pair programming with intelligent model routing
- **Together**: AI coding that follows your project's standards and workflows

For more details on Agent OS capabilities, see: https://github.com/Khamel83/agent-os