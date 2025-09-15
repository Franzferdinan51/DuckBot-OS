#!/usr/bin/env python3
"""
GitHub Spec-Kit Integration for DuckBot
Provides spec-driven development capabilities integrated with Charm ecosystem
"""

import asyncio
import logging
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class SpecKitIntegration:
    """Integration with GitHub Spec-Kit for spec-driven development"""
    
    def __init__(self):
        self.spec_workspace = Path.cwd() / "spec-kit-workspace"
        self.specs_dir = self.spec_workspace / "specs"
        self.implementations_dir = self.spec_workspace / "implementations"
        
        # Ensure directories exist
        self.spec_workspace.mkdir(exist_ok=True)
        self.specs_dir.mkdir(exist_ok=True)
        self.implementations_dir.mkdir(exist_ok=True)
        
        # Integration with Charm tools
        self.charm_available = self._check_charm_integration()
    
    def _check_charm_integration(self) -> bool:
        """Check if Charm tools are available for enhanced spec creation"""
        try:
            from .charm_tools_integration import is_charm_available
            return is_charm_available()
        except ImportError:
            return False
    
    async def create_interactive_spec(self, project_name: str) -> Dict[str, Any]:
        """Create a specification interactively using Charm tools"""
        if not self.charm_available:
            return await self._create_basic_spec(project_name)
        
        try:
            from .charm_tools_integration import (
                gum_input, gum_choose, gum_confirm, gum_write, glow_render
            )
            
            logger.info(f"Creating interactive spec for project: {project_name}")
            
            # Project overview
            print("\n[TARGET] PROJECT SPECIFICATION WIZARD")
            print("=" * 50)
            
            project_type = await gum_choose(
                ["Web Application", "API/Backend", "CLI Tool", "Library/Package", "Data Pipeline", "AI/ML Application"],
                "What type of project are you building?"
            )
            
            description = await gum_input(
                prompt="Project Description: ",
                placeholder="Brief description of what this project does"
            )
            
            objectives = []
            print("\n[LIST] PROJECT OBJECTIVES")
            while True:
                objective = await gum_input(
                    prompt="Add objective (or press Enter to continue): ",
                    placeholder="What should this project accomplish?"
                )
                if not objective:
                    break
                objectives.append(objective)
            
            # Technical requirements
            tech_stack = await gum_input(
                prompt="Preferred tech stack: ",
                placeholder="e.g., Python, FastAPI, React, PostgreSQL"
            )
            
            constraints = []
            has_constraints = await gum_confirm("Do you have any technical constraints or requirements?")
            if has_constraints:
                while True:
                    constraint = await gum_input(
                        prompt="Add constraint (or press Enter to continue): ",
                        placeholder="e.g., Must run on specific OS, performance requirements"
                    )
                    if not constraint:
                        break
                    constraints.append(constraint)
            
            # User scenarios
            scenarios = []
            print("\n[EMOJI] USER SCENARIOS")
            while True:
                scenario = await gum_input(
                    prompt="Add user scenario (or press Enter to continue): ",
                    placeholder="As a [user type], I want to [action] so that [benefit]"
                )
                if not scenario:
                    break
                scenarios.append(scenario)
            
            # Generate spec
            spec = {
                "project_name": project_name,
                "project_type": project_type,
                "description": description,
                "objectives": objectives,
                "tech_stack": tech_stack,
                "constraints": constraints,
                "user_scenarios": scenarios,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # Save spec
            spec_file = self.specs_dir / f"{project_name}_spec.json"
            with open(spec_file, 'w') as f:
                json.dump(spec, f, indent=2)
            
            # Generate markdown spec
            markdown_spec = await self._generate_markdown_spec(spec)
            spec_md_file = self.specs_dir / f"{project_name}_spec.md"
            with open(spec_md_file, 'w') as f:
                f.write(markdown_spec)
            
            # Preview spec
            preview = await gum_confirm("Would you like to preview the generated specification?")
            if preview:
                await glow_render(file_path=str(spec_md_file))
            
            logger.info(f"Specification created: {spec_file}")
            return {
                "success": True,
                "spec_file": str(spec_file),
                "spec": spec
            }
            
        except Exception as e:
            logger.error(f"Failed to create interactive spec: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_basic_spec(self, project_name: str) -> Dict[str, Any]:
        """Create a basic specification without Charm tools"""
        try:
            spec = {
                "project_name": project_name,
                "project_type": "General",
                "description": f"Specification for {project_name}",
                "objectives": ["To be defined"],
                "tech_stack": "To be specified",
                "constraints": [],
                "user_scenarios": [],
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            spec_file = self.specs_dir / f"{project_name}_spec.json"
            with open(spec_file, 'w') as f:
                json.dump(spec, f, indent=2)
            
            return {
                "success": True,
                "spec_file": str(spec_file),
                "spec": spec
            }
            
        except Exception as e:
            logger.error(f"Failed to create basic spec: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_markdown_spec(self, spec: Dict[str, Any]) -> str:
        """Generate markdown specification from spec data"""
        markdown = f"""# {spec['project_name']} - Project Specification

## Overview
- **Type**: {spec['project_type']}
- **Version**: {spec['version']}
- **Created**: {spec['created_at']}

## Description
{spec['description']}

## Objectives
"""
        for obj in spec['objectives']:
            markdown += f"- {obj}\n"
        
        markdown += f"""
## Technical Stack
{spec['tech_stack']}

## Constraints
"""
        for constraint in spec['constraints']:
            markdown += f"- {constraint}\n"
        
        markdown += """
## User Scenarios
"""
        for scenario in spec['user_scenarios']:
            markdown += f"- {scenario}\n"
        
        return markdown
    
    async def generate_implementation_plan(self, spec_file: str) -> Dict[str, Any]:
        """Generate an implementation plan from a specification"""
        try:
            spec_path = Path(spec_file)
            if not spec_path.exists():
                return {"success": False, "error": "Specification file not found"}
            
            with open(spec_path, 'r') as f:
                spec = json.load(f)
            
            # Generate implementation steps
            plan = {
                "project_name": spec["project_name"],
                "implementation_steps": [
                    "1. Set up project structure and dependencies",
                    "2. Implement core functionality",
                    "3. Add user interface components",
                    "4. Implement business logic",
                    "5. Add testing suite",
                    "6. Documentation and deployment setup"
                ],
                "estimated_timeline": "2-4 weeks",
                "key_components": [],
                "testing_strategy": "Unit tests, integration tests, end-to-end tests",
                "deployment_plan": "TBD based on requirements",
                "generated_at": datetime.now().isoformat()
            }
            
            # Save implementation plan
            plan_file = self.implementations_dir / f"{spec['project_name']}_plan.json"
            with open(plan_file, 'w') as f:
                json.dump(plan, f, indent=2)
            
            logger.info(f"Implementation plan generated: {plan_file}")
            return {
                "success": True,
                "plan_file": str(plan_file),
                "plan": plan
            }
            
        except Exception as e:
            logger.error(f"Failed to generate implementation plan: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_specifications(self) -> List[Dict[str, Any]]:
        """List all available specifications"""
        specs = []
        try:
            for spec_file in self.specs_dir.glob("*_spec.json"):
                with open(spec_file, 'r') as f:
                    spec = json.load(f)
                    specs.append({
                        "file": str(spec_file),
                        "name": spec.get("project_name", "Unknown"),
                        "type": spec.get("project_type", "Unknown"),
                        "created": spec.get("created_at", "Unknown")
                    })
        except Exception as e:
            logger.error(f"Failed to list specifications: {e}")
        
        return specs
    
    async def create_spec_driven_workflow(self, project_name: str) -> Dict[str, Any]:
        """Create a complete spec-driven development workflow"""
        if not self.charm_available:
            return {"success": False, "error": "Charm tools not available for workflow creation"}
        
        try:
            from .charm_tools_integration import gum_confirm, vhs_create_demo
            
            # Create specification
            spec_result = await self.create_interactive_spec(project_name)
            if not spec_result.get("success"):
                return spec_result
            
            # Generate implementation plan
            plan_result = await self.generate_implementation_plan(spec_result["spec_file"])
            if not plan_result.get("success"):
                return plan_result
            
            # Optional: Create VHS demo tape
            create_demo = await gum_confirm("Would you like to create a demo recording template?")
            if create_demo:
                demo_result = await vhs_create_demo(f"{project_name}_demo")
                logger.info(f"Demo template created: {demo_result}")
            
            return {
                "success": True,
                "spec_file": spec_result["spec_file"],
                "plan_file": plan_result["plan_file"],
                "workflow_complete": True
            }
            
        except Exception as e:
            logger.error(f"Failed to create spec-driven workflow: {e}")
            return {"success": False, "error": str(e)}
    
    def get_workspace_status(self) -> Dict[str, Any]:
        """Get status of the spec-kit workspace"""
        try:
            specs = list(self.specs_dir.glob("*_spec.json"))
            plans = list(self.implementations_dir.glob("*_plan.json"))
            
            return {
                "workspace_path": str(self.spec_workspace),
                "specifications": len(specs),
                "implementation_plans": len(plans),
                "charm_integration": self.charm_available,
                "total_files": len(specs) + len(plans)
            }
            
        except Exception as e:
            logger.error(f"Failed to get workspace status: {e}")
            return {"error": str(e)}

# Global instance
spec_kit = SpecKitIntegration()

# Convenience functions
async def create_project_spec(project_name: str) -> Dict[str, Any]:
    """Create a new project specification"""
    return await spec_kit.create_interactive_spec(project_name)

async def generate_plan(spec_file: str) -> Dict[str, Any]:
    """Generate implementation plan from specification"""
    return await spec_kit.generate_implementation_plan(spec_file)

async def create_workflow(project_name: str) -> Dict[str, Any]:
    """Create complete spec-driven workflow"""
    return await spec_kit.create_spec_driven_workflow(project_name)

def get_spec_status() -> Dict[str, Any]:
    """Get spec-kit workspace status"""
    return spec_kit.get_workspace_status()

async def list_specs() -> List[Dict[str, Any]]:
    """List all specifications"""
    return await spec_kit.list_specifications()

# Integration with DuckBot services
async def initialize_spec_kit_integration() -> bool:
    """Initialize Spec-Kit integration"""
    try:
        status = spec_kit.get_workspace_status()
        logger.info(f"Spec-Kit workspace initialized: {status['workspace_path']}")
        
        if status.get('charm_integration'):
            logger.info("Spec-Kit successfully integrated with Charm ecosystem!")
            return True
        else:
            logger.warning("Spec-Kit running in basic mode (Charm tools not available)")
            return True
            
    except Exception as e:
        logger.error(f"Failed to initialize Spec-Kit integration: {e}")
        return False