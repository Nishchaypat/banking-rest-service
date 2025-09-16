#!/usr/bin/env python3
"""
Banking API Test Client Application
===================================

This test client demonstrates the complete flow of the banking API,
including user registration, authentication, account management,
transactions, transfers, card operations, and statement generation.

Usage:
    python test_client.py

Requirements:
    - requests library
    - The banking API server running on localhost:8000 (or modify BASE_URL)
"""

import requests
import json
import time
import csv
from io import StringIO
from datetime import datetime
import sys

class BankingTestClient:
    def __init__(self, base_url="http://127.0.0.1:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {}
        
    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
        
    def print_step(self, step, description):
        print(f"\nStep {step}: {description}")
        print("-" * 40)
        
    def print_response(self, response, show_content=True):
        print(f"Status: {response.status_code}")
        if show_content:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except json.JSONDecodeError:
                print(f"Response: {response.text}")
        print()
        
    def signup(self, username, password, full_name):
        """Register a new user"""
        url = f"{self.base_url}/signup"
        data = {
            "username": username,
            "password": password,
            "full_name": full_name
        }
        
        response = self.session.post(url, json=data)
        self.print_response(response)
        return response.status_code == 200
        
    def login(self, username, password):
        """Login and get authentication token"""
        url = f"{self.base_url}/token"
        data = {
            "username": username,
            "password": password
        }
        
        response = self.session.post(url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.auth_token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.auth_token}"}
            print(f"Login successful! Token: {self.auth_token[:20]}...")
            return True
        else:
            self.print_response(response)
            return False
            
    def create_account(self, initial_balance):
        """Create a new bank account"""
        url = f"{self.base_url}/accounts"
        data = {"initial_balance": initial_balance}
        
        response = self.session.post(url, json=data, headers=self.headers)
        self.print_response(response)
        return response.status_code == 200
        
    def list_accounts(self):
        """List all accounts for the authenticated user"""
        url = f"{self.base_url}/accounts"
        
        response = self.session.get(url, headers=self.headers)
        self.print_response(response)
        
        if response.status_code == 200:
            accounts = response.json().get("accounts", [])
            return accounts[0]["id"] if accounts else None
        return None
        
    def create_transaction(self, account_id, transaction_type, amount):
        """Create a transaction (deposit or withdrawal)"""
        url = f"{self.base_url}/transactions"
        data = {
            "account_id": account_id,
            "type": transaction_type,
            "amount": amount
        }
        
        response = self.session.post(url, json=data, headers=self.headers)
        self.print_response(response)
        return response.status_code == 200
        
    def external_transfer(self, from_account_id, external_account, amount):
        """Perform external transfer"""
        url = f"{self.base_url}/external-transfer"
        data = {
            "from_account_id": from_account_id,
            "external_account": external_account,
            "amount": amount
        }
        
        response = self.session.post(url, json=data, headers=self.headers)
        self.print_response(response)
        return response.status_code == 200
        
    def create_card(self, account_id, card_type, expiry):
        """Create a new card and return its details"""
        url = f"{self.base_url}/cards"
        data = {
            "account_id": account_id,
            "card_type": card_type,
            "expiry": expiry
        }
        
        response = self.session.post(url, json=data, headers=self.headers)
        self.print_response(response)
        
        if response.status_code == 200:
            return response.json() # Return the full card object
        return None
        
    def update_card_status(self, card_id, status):
        """Update card status"""
        url = f"{self.base_url}/cards/{card_id}/status"
        data = {"status": status}
        
        response = self.session.put(url, json=data, headers=self.headers)
        self.print_response(response)
        return response.status_code == 200
        
    def update_card_pin(self, card_id, pin):
        """Update card PIN"""
        url = f"{self.base_url}/cards/{card_id}/pin"
        data = {"pin": pin}
        
        response = self.session.put(url, json=data, headers=self.headers)
        self.print_response(response)
        return response.status_code == 200
        
    def delete_card(self, card_id):
        """Delete a card"""
        url = f"{self.base_url}/cards/{card_id}"
        
        response = self.session.delete(url, headers=self.headers)
        self.print_response(response)
        return response.status_code == 200
        
    def get_monthly_statement(self, account_id, year, month):
        """Get monthly statement"""
        url = f"{self.base_url}/statements/{account_id}/monthly"
        params = {"year": year, "month": month}
        
        response = self.session.get(url, params=params, headers=self.headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Statement Content (CSV):")
            print(response.text)
            
            # Parse CSV content
            try:
                csv_reader = csv.reader(StringIO(response.text))
                rows = list(csv_reader)
                print(f"Total rows: {len(rows)}")
                if len(rows) > 1:
                    print(f"Transactions found: {len(rows) - 1}")
            except Exception as e:
                print(f"Could not parse CSV: {e}")
        else:
            self.print_response(response, show_content=True)
        
        return response.status_code == 200

    def run_demo(self):
        """Run the complete demo flow"""
        timestamp = int(time.time())
        username = f"demo_user_{timestamp}"
        password = "DemoPassword123!"
        full_name = "Demo User"
        
        self.print_section("BANKING API TEST CLIENT DEMO")
        print(f"Testing with user: {username}")
        
        # Step 1: User Registration
        self.print_step(1, "User Registration")
        if not self.signup(username, password, full_name):
            print(" Registration failed! The user might already exist. Trying to log in...")
            # If signup fails (e.g., user exists), try to log in instead of stopping
            if not self.login(username, password):
                print(" Login also failed! Halting test.")
                return False
        else:
            print(" Registration successful!")
            # Step 2: User Login
            self.print_step(2, "User Login")
            if not self.login(username, password):
                print(" Login failed!")
                return False
        
        print(" Login successful!")
        
        # Step 3: Create Bank Account
        self.print_step(3, "Create Bank Account")
        if not self.create_account(2500.0):
            print(" Account creation failed!")
            return False
            
        print(" Account created successfully!")
        
        # Step 4: List Accounts and Get Account ID
        self.print_step(4, "List Accounts")
        account_id = self.list_accounts()
        if not account_id:
            print(" Could not retrieve account ID!")
            return False
            
        print(f" Account ID retrieved: {account_id}")
        
        # Step 5: Perform Transactions
        self.print_step(5, "Perform Transactions")
        
        print("5a. Making deposit of $500...")
        if not self.create_transaction(account_id, "deposit", 500.0):
            print(" Deposit failed!")
            return False
        print(" Deposit successful!")
        
        print("5b. Making withdrawal of $200...")
        if not self.create_transaction(account_id, "withdrawal", 200.0):
            print(" Withdrawal failed!")
            return False
        print(" Withdrawal successful!")
        
        # Step 6: External Transfer
        self.print_step(6, "External Transfer")
        if not self.external_transfer(account_id, "EXTERNAL12345678", 300.0):
            print(" External transfer failed!")
            return False
        print(" External transfer successful!")
        
        # Step 7: Card Operations
        self.print_step(7, "Card Operations (Full Lifecycle)")
        
        print("7a. Creating a new debit card...")
        card_info = self.create_card(account_id, "debit", "12/28")
        if not card_info:
            print(" Card creation failed!")
            return False
            
        card_id = card_info.get("id")
        card_number = card_info.get("card_number")
        
        
        if not card_id or not card_number:
            print(" Card response did not contain 'id' or 'card_number'!")
            return False
        print(f" Debit card created: {card_number} with ID: {card_id}")
        
        print("7b. Updating card status to 'blocked'...")
        if not self.update_card_status(card_id, "blocked"):
            print(" Failed to update card status!")
            return False
        print(" Card status updated successfully!")
        
        print("7c. Updating card PIN...")
        if not self.update_card_pin(card_id, "4321"):
            print(" Failed to update card PIN!")
            return False
        print(" Card PIN updated successfully!")
        
        print("7d. Deleting the card...")
        if not self.delete_card(card_id):
            print("Failed to delete the card!")
            return False
        print("Card deleted successfully!")
        
        # Step 8: Generate Monthly Statement
        self.print_step(8, "Generate Monthly Statement")
        now = datetime.utcnow()
        year, month = now.year, now.month
        
        if not self.get_monthly_statement(account_id, year, month):
            print("Statement generation failed!")
            return False
        print("Monthly statement generated successfully!")
        
        # Step 9: Error Handling Demo
        self.print_step(9, "Error Handling Demo")
        
        print("9a. Attempting withdrawal with insufficient funds...")
        self.create_transaction(account_id, "withdrawal", 999999.0)
        
        print("9b. Attempting external transfer with insufficient funds...")
        self.external_transfer(account_id, "EXTERNAL12345678", 999999.0)
        
        print("9c. Attempting to get statement for a non-existent account...")
        self.get_monthly_statement("non-existent-id", 2023, 1)
        
        print("Error handling demonstrated!")
        
        self.print_section("DEMO COMPLETED SUCCESSFULLY! 🎉")
        return True

    def run_stress_test(self):
        """Run stress test with multiple operations"""
        self.print_section("STRESS TEST MODE")
        
        timestamp = int(time.time())
        username = f"stress_user_{timestamp}"
        password = "StressPassword123!"
        full_name = "Stress Test User"
        
        if not self.signup(username, password, full_name): return False
        if not self.login(username, password): return False
        if not self.create_account(50000.0): return False
            
        account_id = self.list_accounts()
        if not account_id: return False
            
        print(f"Performing 20 rapid transactions for account {account_id}...")
        success_count = 0
        
        for i in range(20):
            if i % 2 == 0:
                success = self.create_transaction(account_id, "deposit", 50.0)
            else:
                success = self.create_transaction(account_id, "withdrawal", 25.0)
                
            if success:
                success_count += 1
                
        print(f"{success_count}/20 transactions successful!")
        
        now = datetime.utcnow()
        self.get_monthly_statement(account_id, now.year, now.month)
        
        print("Stress test completed!")
        return True


def main():
    """Main function to run the test client"""
    print("Banking API Test Client")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--stress":
        mode = "stress"
    else:
        mode = "demo"
        
    base_url = "http://127.0.0.1:8001"
    client = BankingTestClient(base_url)
    
    try:
        if mode == "stress":
            success = client.run_stress_test()
        else:
            success = client.run_demo()
            
        if success:
            print("\nAll tests completed successfully!")
            sys.exit(0)
        else:
            print("\nOne or more steps failed. Please review the output.")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"\nCould not connect to the API server at {base_url}")
        print("Please ensure the banking API server is running.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()