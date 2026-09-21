# Campus Placement AI Agent

## Overview
Campus Placement AI Agent is a multi-agent AI system built using Microsoft Foundry to help students prepare for campus placements.

The system uses a Main Placement Agent that coordinates specialized sub-agents.

## Features

### 1. Resume Analysis
- Analyzes the student's resume
- Identifies skills and projects
- Finds missing or weak information
- Provides improvement suggestions

### 2. Interview Preparation
- Generates technical interview questions
- Generates HR interview questions
- Provides feedback on student answers

## Agents

### Main Placement Agent
The main orchestrator that understands the student's request and assigns tasks to the appropriate sub-agents.

### Resume Analysis Agent
Analyzes the student's resume and provides feedback and improvement suggestions.

### Interview Preparation Agent
Generates interview questions based on the student's skills and helps the student prepare for interviews.

## Workflow

Student Request  
↓  
Main Placement Agent  
↓  
Resume Analysis Agent + Interview Preparation Agent  
↓  
Main Placement Agent combines the results  
↓  
Final Response

## Technologies Used
- Microsoft Foundry
- Azure AI
- Python
- GitHub

## Project Goal
The goal of this project is to demonstrate a multi-agent system where specialized AI agents work together to help students prepare for campus placements.
