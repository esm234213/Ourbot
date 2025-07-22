# Replit.md

## Overview

This repository contains a Telegram bot built with Python that serves as an application system for team recruitment. The bot allows users to apply to different teams within an organization called "Our Goal" and provides administrative capabilities for managing applications. The system is designed to handle multi-step conversations, data persistence, and admin notifications.

## User Preferences

Preferred communication style: Simple, everyday language.
Welcome message preference: Updated to use more welcoming and encouraging Arabic text style.
Team naming preference: Use "تيم" instead of "فريق" for team names. 
Active teams: 4 teams only - تيم الاختبارات, تيم التجميعات, تيم السوشيال, تيم الدعم الفني.
Two-way communication: Admin replies to forwarded applications should be sent back to applicants automatically.
Menu system: Added /menu command and bot menu button for easy navigation.
Admin decision system: Added accept/reject buttons to admin notifications for quick application processing.
Full chat system: Users can reply to admin messages, creating ongoing conversations until admin ends them with a button.
Clear applications feature: Added /clear command for admins to reset all applications and allow users to reapply.

## System Architecture

### Core Framework
- **Language**: Python 3.x
- **Main Library**: python-telegram-bot for Telegram API integration
- **Environment Management**: python-dotenv for configuration
- **Data Storage**: JSON files for persistent data storage
- **Logging**: Python's built-in logging module

### Architecture Pattern
The application follows a modular architecture with clear separation of concerns:
- **Configuration Management**: Centralized in `config.py`
- **Data Layer**: Abstracted through `DataManager` class
- **Business Logic**: Handled in `handlers.py`
- **Application Entry Point**: `main.py` orchestrates the bot lifecycle

## Key Components

### 1. Configuration System (`config.py`)
- Manages environment variables and bot settings
- Defines team structures and conversation states
- Contains Arabic message templates for user interactions
- Handles bot token and admin group configuration

### 2. Data Management (`data_manager.py`)
- **DataManager Class**: Handles all data persistence operations
- **Storage Format**: JSON files for applications, users, and statistics
- **Key Methods**:
  - Application validation and storage
  - User application history tracking
  - Data loading and saving with error handling

### 3. Message Handlers (`handlers.py`)
- **Conversation Flow**: Multi-step application process using ConversationHandler
- **Team Selection**: Inline keyboard for team choice
- **Input Processing**: Handles user responses for application questions
- **Admin Integration**: Forwards applications to admin group
- **Application Management**: Clear all applications with /clear command (admin only)

### 4. Application Entry (`main.py`)
- **Bot Initialization**: Sets up Telegram bot application
- **Handler Registration**: Configures conversation handlers and commands
- **Error Handling**: Implements graceful error management

### 5. Legacy Component (`attached_assets/bot_1752687387240.py`)
- Contains additional bot functionality (appears to be a previous version)
- Includes user tracking and message forwarding features

## Data Flow

### Application Process
1. User starts with `/start` command
2. Bot displays welcome message with team selection buttons
3. User selects team → Bot asks for application reason
4. User provides reason → Bot asks for experience
5. User provides experience → Application is saved and forwarded to admin
6. Confirmation sent to user

### Data Storage Flow
1. User interactions are captured in handlers
2. DataManager validates and processes data
3. Applications stored in JSON format with timestamps
4. Admin notifications sent to designated group

## External Dependencies

### Core Libraries
- `python-telegram-bot`: Telegram Bot API wrapper
- `python-dotenv`: Environment variable management
- `json`: Data serialization (built-in)
- `logging`: Application logging (built-in)
- `datetime`: Timestamp management (built-in)

### Environment Variables
- `BOT_TOKEN`: Telegram bot authentication token
- `ADMIN_GROUP_ID`: Telegram group ID for admin notifications

## Deployment Strategy

### File Structure
```
/
├── config.py           # Configuration and constants
├── data_manager.py     # Data persistence layer
├── handlers.py         # Message and callback handlers
├── main.py            # Application entry point
├── applications.json  # Application data (created at runtime)
├── users.json         # User data (created at runtime)
├── stats.json         # Statistics data (created at runtime)
└── attached_assets/   # Legacy code and assets
```

### Runtime Requirements
- Python 3.7+ environment
- Environment variables configured
- Write permissions for JSON file creation
- Network access for Telegram API communication

### Key Architectural Decisions

1. **JSON File Storage**: Chosen for simplicity and portability over database systems
   - Pros: Easy to implement, version control friendly, no additional dependencies
   - Cons: Limited scalability, no transaction support

2. **Conversation State Management**: Uses telegram-bot's ConversationHandler
   - Pros: Built-in state management, easy to follow conversation flow
   - Cons: State lost on bot restart

3. **Arabic Language Support**: Full UTF-8 support with Arabic messages
   - Addressed requirement for Arabic-speaking users
   - Ensures proper text encoding and display

4. **Modular Architecture**: Separated concerns across multiple files
   - Improves maintainability and testability
   - Makes code easier to understand and extend

5. **Admin Integration**: Automatic forwarding to admin group
   - Provides real-time notification system
   - Centralizes application review process