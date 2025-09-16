# AI Tools Report - Banking API Development

This report shows how AI tools helped build the banking API from start to finish.

## Project Organization

**Perplexity Space Setup**
Created a dedicated workspace 'Spaces' in Perplexity to keep all project files, docs, and decisions in one place. This made it easy to find information and stay organized throughout development.

## Where AI Was Used

### 1. Planning Features and Choosing Technology

**What was done manually:**
- Made a basic list of features needed (login, accounts, cards, transactions)
- Picked some initial technologies

**How AI helped:**
Asked Perplexity to review the plan and suggest improvements.

**Example prompt:**
> "I'm building a banking API with these features: user login, accounts, transactions, cards. What am I missing for security and compliance? What's the best Python stack?"

**AI provided:**
- Better security recommendations with password hashing algorithms
- Modern Python tools to use: Pydantic

### 2. Setting Up Project Structure

**Example prompt:**
> "Can you create a folder structure for my banking API? I need separate modules for accounts, transactions, cards, and auth. Show me what files go where."

**AI created:**
- Complete directory layout
- Sample code files for each module

### 3. Building and Reviewing Code

**Example prompt:**
> "Here's my money transfer endpoint. Am I handling all the edge cases? What about security and error handling?"

**AI caught issues like:**
- No rollback for failed transactions

### 4. Creating Tests

**What was done manually:**
- Listed what needed testing

**How AI helped:**

**Example prompt:**
> "Write pytest tests for my auth and account modules. Include edge cases and error handling tests."

**AI provided:**
- Complete test suites
- Edge case scenarios we missed
- Security testing suggestions

## Tools Used

- **Perplexity**: Main tool for planning and documenting
- **Comet**: Better research and tips
- **Claude Code**: Converting requirements to code

## Example Conversations

| What Was Asked | What Happened |
|---------------|---------------|
| "Make a FastAPI endpoint for deposits" | Got basic code but missed negative amount validation, had to ask for improvements |
| "Is my endpoint secure enough?" | AI confirmed JWT security was good, suggested better error messages |
| "Create file structure for accounts module" | Got complete structure, then manually connected everything |
| "Based on the info you have on this entire Space, write me the following README.me" | Got overview of all the README needed, then manually corrected and reasoned |

## Problems AI Helped Solve

**Connecting Different Parts:**
- **Problem**: Making sure all modules worked together properly
- **AI Solution**: Reviewed code for consistency and suggested fixes

**Security Requirements:**
- **Problem**: Making sure all security basics were covered
- **AI Solution**: Provided checklists and example code for password hashing, rate limiting, etc.

**Test Coverage:**
- **Problem**: Missing important test scenarios
- **AI Solution**: Generated 4-5 of test cases that weren't thought of

## What Was Still Done Manually

- Overall logic and flow of the system
- Final decisions on project structure
- Setting up test suit with different database and endpoint
- Manual testing using CURL

## Summary

AI tools, especially Perplexity, helped plan better, write more secure code, and create thorough tests. But my judgment was still needed for editing code, API handeling, final implementation details. This combination of AI assistance and human oversight made development much faster and more reliable.