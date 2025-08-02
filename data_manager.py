#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import shutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from config import APPLICATIONS_FILE, USERS_FILE, STATS_FILE, COOLDOWN_HOURS, BANNED_USERS_FILE

logger = logging.getLogger(__name__)

class DataManager:
    """Handle data persistence for the bot with enhanced features."""
    
    def __init__(self):
        self.applications = self._load_json(APPLICATIONS_FILE, [])
        self.users = self._load_json(USERS_FILE, {})
        self.stats = self._load_json(STATS_FILE, {})
        self.banned_users = self._load_json(BANNED_USERS_FILE, [])
        self._ensure_data_integrity()
    
    def _load_json(self, filename: str, default_value: Any) -> Any:
        """Load JSON data from file with error handling."""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    logger.info(f"Successfully loaded {filename}")
                    return data
            logger.info(f"File {filename} not found, using default value")
            return default_value
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filename}: {e}")
            return default_value
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return default_value
    
    def _save_json(self, filename: str, data: Any) -> bool:
        """Save data to JSON file with backup."""
        try:
            # Create backup if file exists
            if os.path.exists(filename):
                backup_name = f"{filename}.backup"
                os.rename(filename, backup_name)
            
            # Save new data
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            # Restore backup if save failed
            backup_name = f"{filename}.backup"
            if os.path.exists(backup_name):
                os.rename(backup_name, filename)
                logger.info(f"Restored backup for {filename}")
            return False
    
    def _ensure_data_integrity(self):
        """Ensure data integrity and fix any issues."""
        try:
            # Validate applications structure
            valid_applications = []
            for app in self.applications:
                if self._validate_application(app):
                    valid_applications.append(app)
                else:
                    logger.warning(f"Removed invalid application: {app}")
            
            if len(valid_applications) != len(self.applications):
                self.applications = valid_applications
                self._save_json(APPLICATIONS_FILE, self.applications)
                logger.info("Fixed applications data integrity")
            
            # Validate users structure
            valid_users = {}
            for user_id, user_data in self.users.items():
                if self._validate_user_data(user_data):
                    valid_users[user_id] = user_data
                else:
                    logger.warning(f"Removed invalid user data for {user_id}")
            
            if len(valid_users) != len(self.users):
                self.users = valid_users
                self._save_json(USERS_FILE, self.users)
                logger.info("Fixed users data integrity")
                
        except Exception as e:
            logger.error(f"Error ensuring data integrity: {e}")
    
    def _validate_application(self, app: dict) -> bool:
        """Validate application data structure."""
        required_fields = ['user_info', 'selected_team', 'team_name', 'reason', 'experience', 'timestamp']
        return all(field in app for field in required_fields)
    
    def _validate_user_data(self, user_data: dict) -> bool:
        """Validate user data structure."""
        required_fields = ['first_name', 'first_seen', 'applications']
        return all(field in user_data for field in required_fields)
    
    def has_user_applied(self, user_id: int, team_id: str) -> bool:
        """Check if user has already applied to a specific team."""
        for application in self.applications:
            if (application['user_info']['user_id'] == user_id and 
                application['selected_team'] == team_id):
                return True
        return False
    
    def can_user_reapply(self, user_id: int, team_id: str) -> bool:
        """Check if user can reapply to a team (after cooldown period)."""
        if not self.has_user_applied(user_id, team_id):
            return True
        
        # Find the latest application for this team
        latest_application = None
        for application in self.applications:
            if (application['user_info']['user_id'] == user_id and 
                application['selected_team'] == team_id):
                if not latest_application or application['timestamp'] > latest_application['timestamp']:
                    latest_application = application
        
        if not latest_application:
            return True
        
        # Check cooldown period
        try:
            app_time = datetime.fromisoformat(latest_application['timestamp'])
            cooldown_end = app_time + timedelta(hours=COOLDOWN_HOURS)
            return datetime.now() >= cooldown_end
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return True
    
    def save_application(self, application_data: dict) -> bool:
        """Save a new application with enhanced validation."""
        try:
            # Validate application data
            if not self._validate_application(application_data):
                logger.error("Invalid application data structure")
                return False
            
            # Add unique ID to application
            application_data['id'] = f"{application_data['user_info']['user_id']}_{application_data['selected_team']}_{int(datetime.now().timestamp())}"
            
            # Add application to list
            self.applications.append(application_data)
            
            # Update user data
            user_id = str(application_data['user_info']['user_id'])
            if user_id not in self.users:
                self.users[user_id] = {
                    'first_name': application_data['user_info']['first_name'],
                    'last_name': application_data['user_info']['last_name'],
                    'username': application_data['user_info']['username'],
                    'first_seen': application_data['timestamp'],
                    'applications': [],
                    'total_applications': 0
                }
            
            # Add this application to user's applications
            self.users[user_id]['applications'].append({
                'id': application_data['id'],
                'team_id': application_data['selected_team'],
                'team_name': application_data['team_name'],
                'timestamp': application_data['timestamp']
            })
            
            # Update user stats
            self.users[user_id]['total_applications'] = len(self.users[user_id]['applications'])
            self.users[user_id]['last_active'] = application_data['timestamp']
            
            # Save to files
            success = (self._save_json(APPLICATIONS_FILE, self.applications) and 
                      self._save_json(USERS_FILE, self.users))
            
            if success:
                logger.info(f"Successfully saved application for user {user_id} to team {application_data['selected_team']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save application: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive application statistics."""
        try:
            # Count applications by team
            team_counts = {}
            unique_users = set()
            recent_applications = 0
            
            # Calculate recent applications (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            
            for application in self.applications:
                team_id = application['selected_team']
                team_counts[team_id] = team_counts.get(team_id, 0) + 1
                unique_users.add(application['user_info']['user_id'])
                
                # Check if application is recent
                try:
                    app_time = datetime.fromisoformat(application['timestamp'])
                    if app_time >= week_ago:
                        recent_applications += 1
                except Exception:
                    pass
            
            return {
                'total_applications': len(self.applications),
                'total_users': len(unique_users),
                'recent_applications': recent_applications,
                'team_counts': team_counts,
                'active_users': len([u for u in self.users.values() if self._is_user_active(u)])
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                'total_applications': 0,
                'total_users': 0,
                'recent_applications': 0,
                'team_counts': {},
                'active_users': 0
            }
    
    def _is_user_active(self, user_data: dict) -> bool:
        """Check if user is considered active (activity in last 30 days)."""
        try:
            if 'last_active' not in user_data:
                return False
            
            last_active = datetime.fromisoformat(user_data['last_active'])
            month_ago = datetime.now() - timedelta(days=30)
            return last_active >= month_ago
        except Exception:
            return False
    
    def get_user_applications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all applications for a specific user."""
        user_applications = []
        for application in self.applications:
            if application['user_info']['user_id'] == user_id:
                user_applications.append(application)
        return sorted(user_applications, key=lambda x: x['timestamp'], reverse=True)
    
    def get_user_status(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user status."""
        user_id_str = str(user_id)
        user_data = self.users.get(user_id_str, {})
        applications = self.get_user_applications(user_id)
        
        return {
            'user_id': user_id,
            'user_data': user_data,
            'applications': applications,
            'total_applications': len(applications),
            'teams_applied': list(set(app['selected_team'] for app in applications))
        }
    
    def get_team_applications(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all applications for a specific team."""
        team_applications = []
        for application in self.applications:
            if application['selected_team'] == team_id:
                team_applications.append(application)
        return sorted(team_applications, key=lambda x: x['timestamp'], reverse=True)
    
    def get_all_users(self) -> List[int]:
        """Get list of all user IDs."""
        return [int(user_id) for user_id in self.users.keys()]
    
    def clear_applications(self) -> bool:
        """Clear all applications data with backup."""
        try:
            # Create backup before clearing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backup_{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup existing data
            if os.path.exists(APPLICATIONS_FILE):
                shutil.copy2(APPLICATIONS_FILE, f"{backup_dir}/applications.json")
            if os.path.exists(USERS_FILE):
                shutil.copy2(USERS_FILE, f"{backup_dir}/users.json")
            
            # Clear applications and users data
            self.applications = []
            self.users = {}
            
            # Save empty data to files
            success = (self._save_json(APPLICATIONS_FILE, self.applications) and 
                      self._save_json(USERS_FILE, self.users))
            
            if success:
                logger.info(f"Successfully cleared all applications. Backup saved to {backup_dir}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to clear applications: {e}")
            return False
    
    def delete_application(self, application_id: str) -> bool:
        """Delete a specific application."""
        try:
            # Find and remove application
            original_count = len(self.applications)
            self.applications = [app for app in self.applications if app.get('id') != application_id]
            
            if len(self.applications) == original_count:
                logger.warning(f"Application {application_id} not found")
                return False
            
            # Update user data
            for user_id, user_data in self.users.items():
                user_data['applications'] = [app for app in user_data['applications'] if app.get('id') != application_id]
                user_data['total_applications'] = len(user_data['applications'])
            
            # Save updated data
            success = (self._save_json(APPLICATIONS_FILE, self.applications) and 
                      self._save_json(USERS_FILE, self.users))
            
            if success:
                logger.info(f"Successfully deleted application {application_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete application {application_id}: {e}")
            return False



    def ban_user(self, user_id: int) -> bool:
        """Add a user to the banned list."""
        user_id_str = str(user_id)
        if user_id_str not in self.banned_users:
            self.banned_users.append(user_id_str)
            return self._save_json(BANNED_USERS_FILE, self.banned_users)
        return False

    def unban_user(self, user_id: int) -> bool:
        """Remove a user from the banned list."""
        user_id_str = str(user_id)
        if user_id_str in self.banned_users:
            self.banned_users.remove(user_id_str)
            return self._save_json(BANNED_USERS_FILE, self.banned_users)
        return False

    def is_user_banned(self, user_id: int) -> bool:
        """Check if a user is banned."""
        return str(user_id) in self.banned_users


