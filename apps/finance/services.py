from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from apps.finance.models import (
    get_user_categories, create_category, update_category, delete_category,
    get_transaction, get_user_transactions, create_transaction, update_transaction, delete_transaction,
    get_budget, get_user_budgets, create_budget, update_budget, delete_budget, get_budget_status,
    get_expense_summary_by_category, get_monthly_summary
)
from database.models import (
    User, Category, Transaction, Budget,
    TransactionType
)

# Setup logger
logger = logging.getLogger("finance")

class CategoryService:
    """Service for managing expense and income categories."""
    
    @staticmethod
    async def get_categories(
        user_id: int,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Category]:
        """Get all categories for a user."""
        logger.info(f"Getting categories for user {user_id}, type={transaction_type}")
        return await get_user_categories(user_id=user_id, transaction_type=transaction_type)
    
    @staticmethod
    async def create_category(
        user_id: int,
        name: str,
        transaction_type: Optional[TransactionType] = None,
        icon: Optional[str] = None,
        color: str = "#4A6FFF"
    ) -> Optional[Category]:
        """Create a new category."""
        logger.info(f"Creating category for user {user_id}: {name}, type={transaction_type}")
        return await create_category(
            user_id=user_id,
            name=name,
            transaction_type=transaction_type,
            icon=icon,
            color=color
        )
    
    @staticmethod
    async def update_category(
        category_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Category]:
        """Update an existing category."""
        logger.info(f"Updating category {category_id} for user {user_id}")
        return await update_category(category_id=category_id, user_id=user_id, **kwargs)
    
    @staticmethod
    async def delete_category(category_id: int, user_id: int) -> bool:
        """Delete a category."""
        logger.info(f"Deleting category {category_id} for user {user_id}")
        return await delete_category(category_id=category_id, user_id=user_id)
    
    @staticmethod
    async def get_default_categories(user_id: int) -> List[Category]:
        """Create default categories for a new user."""
        logger.info(f"Creating default categories for user {user_id}")
        
        # Define default categories
        default_expense_categories = [
            {"name": "Food & Dining", "icon": "🍔", "color": "#FF5733"},
            {"name": "Transportation", "icon": "🚗", "color": "#3366FF"},
            {"name": "Housing", "icon": "🏠", "color": "#33FF57"},
            {"name": "Entertainment", "icon": "🎬", "color": "#FF33A8"},
            {"name": "Shopping", "icon": "🛍️", "color": "#A833FF"},
            {"name": "Health", "icon": "⚕️", "color": "#33FFF3"},
            {"name": "Travel", "icon": "✈️", "color": "#F3FF33"},
            {"name": "Education", "icon": "📚", "color": "#FF8333"},
            {"name": "Bills & Utilities", "icon": "📱", "color": "#3380FF"}
        ]
        
        default_income_categories = [
            {"name": "Salary", "icon": "💰", "color": "#33FF57"},
            {"name": "Freelance", "icon": "💻", "color": "#3366FF"},
            {"name": "Gifts", "icon": "🎁", "color": "#FF33A8"},
            {"name": "Investments", "icon": "📈", "color": "#F3FF33"},
            {"name": "Rental Income", "icon": "🏢", "color": "#A833FF"}
        ]
        
        # Create expense categories
        expense_categories = []
        for cat in default_expense_categories:
            category = await create_category(
                user_id=user_id,
                name=cat["name"],
                transaction_type=TransactionType.EXPENSE,
                icon=cat["icon"],
                color=cat["color"]
            )
            if category:
                expense_categories.append(category)
        
        # Create income categories
        income_categories = []
        for cat in default_income_categories:
            category = await create_category(
                user_id=user_id,
                name=cat["name"],
                transaction_type=TransactionType.INCOME,
                icon=cat["icon"],
                color=cat["color"]
            )
            if category:
                income_categories.append(category)
        
        return expense_categories + income_categories


class FinanceService:
    """Service for managing financial transactions."""
    
    @staticmethod
    async def get_transaction(transaction_id: int, user_id: int) -> Optional[Transaction]:
        """Get a transaction by ID."""
        logger.info(f"Getting transaction {transaction_id} for user {user_id}")
        return await get_transaction(transaction_id=transaction_id, user_id=user_id)
    
    @staticmethod
    async def get_transactions(
        user_id: int,
        **kwargs
    ) -> List[Transaction]:
        """Get transactions for a user with filters."""
        logger.info(f"Getting transactions for user {user_id} with filters")
        return await get_user_transactions(user_id=user_id, **kwargs)
        
    @staticmethod
    async def get_transaction_count(user_id: int) -> int:
        """Get total count of transactions for a user."""
        logger.info(f"Getting transaction count for user {user_id}")
        try:
            user = await User.get(telegram_id=user_id)
            return await Transaction.filter(user=user).count()
        except Exception as e:
            logger.error(f"Error getting transaction count: {e}")
            return 0
    
    @staticmethod
    async def create_transaction(
        user_id: int,
        amount: Decimal,
        transaction_type: TransactionType,
        date: date,
        **kwargs
    ) -> Optional[Transaction]:
        """Create a new transaction."""
        logger.info(f"Creating transaction for user {user_id}: {amount} {kwargs.get('currency', 'USD')}, type={transaction_type}")
        return await create_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            date=date,
            **kwargs
        )
    
    @staticmethod
    async def update_transaction(
        transaction_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Transaction]:
        """Update an existing transaction."""
        logger.info(f"Updating transaction {transaction_id} for user {user_id}")
        return await update_transaction(transaction_id=transaction_id, user_id=user_id, **kwargs)
    
    @staticmethod
    async def delete_transaction(transaction_id: int, user_id: int) -> bool:
        """Delete a transaction."""
        logger.info(f"Deleting transaction {transaction_id} for user {user_id}")
        return await delete_transaction(transaction_id=transaction_id, user_id=user_id)
    
    @staticmethod
    async def get_monthly_summary(
        user_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get financial summary for a specific month."""
        # Default to current month if not specified
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month
            
        logger.info(f"Getting monthly summary for user {user_id}: {year}-{month}")
        return await get_monthly_summary(
            user_id=user_id,
            year=year,
            month=month,
            currency=currency
        )
    
    @staticmethod
    async def get_expense_summary(
        user_id: int,
        date_from: date,
        date_to: date,
        currency: str = "USD"
    ) -> List[Dict[str, Any]]:
        """Get expense summary grouped by category."""
        logger.info(f"Getting expense summary for user {user_id}: {date_from} to {date_to}")
        return await get_expense_summary_by_category(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            currency=currency
        )
    
    @staticmethod
    async def get_trend_data(
        user_id: int,
        months: int = 6,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get financial trend data for the last N months."""
        logger.info(f"Getting trend data for user {user_id} for last {months} months")
        
        # Calculate date range
        today = date.today()
        end_month = today.month
        end_year = today.year
        
        # Initialize data structure for results
        trend_data = {
            "labels": [],
            "income": [],
            "expenses": [],
            "balance": []
        }
        
        # Get data for each month
        for i in range(months - 1, -1, -1):
            # Calculate year and month
            month_offset = (end_month - i - 1) % 12 + 1
            year_offset = end_year - (i + end_month - 1) // 12
            
            # Get summary for this month
            summary = await get_monthly_summary(
                user_id=user_id,
                year=year_offset,
                month=month_offset,
                currency=currency
            )
            
            # Add to trend data
            month_label = f"{month_offset:02d}/{year_offset}"
            trend_data["labels"].append(month_label)
            trend_data["income"].append(float(summary["income"]))
            trend_data["expenses"].append(float(summary["expenses"]))
            trend_data["balance"].append(float(summary["balance"]))
        
        return trend_data


class BudgetService:
    """Service for managing financial budgets."""
    
    @staticmethod
    async def get_budget(budget_id: int, user_id: int) -> Optional[Budget]:
        """Get a budget by ID."""
        logger.info(f"Getting budget {budget_id} for user {user_id}")
        return await get_budget(budget_id=budget_id, user_id=user_id)
    
    @staticmethod
    async def get_budgets(
        user_id: int,
        active_only: bool = True,
        category_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> List[Budget]:
        """Get budgets for a user."""
        logger.info(f"Getting budgets for user {user_id}, active_only={active_only}")
        return await get_user_budgets(
            user_id=user_id,
            active_only=active_only,
            category_id=category_id,
            project_id=project_id
        )
    
    @staticmethod
    async def create_budget(
        user_id: int,
        name: str,
        amount: Decimal,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> Optional[Budget]:
        """Create a new budget."""
        logger.info(f"Creating budget for user {user_id}: {name}, amount={amount}")
        return await create_budget(
            user_id=user_id,
            name=name,
            amount=amount,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
    
    @staticmethod
    async def update_budget(
        budget_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Budget]:
        """Update an existing budget."""
        logger.info(f"Updating budget {budget_id} for user {user_id}")
        return await update_budget(budget_id=budget_id, user_id=user_id, **kwargs)
    
    @staticmethod
    async def delete_budget(budget_id: int, user_id: int) -> bool:
        """Delete a budget."""
        logger.info(f"Deleting budget {budget_id} for user {user_id}")
        return await delete_budget(budget_id=budget_id, user_id=user_id)
    
    @staticmethod
    async def get_budget_status(budget_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a budget with spending details."""
        logger.info(f"Getting budget status for budget {budget_id}, user {user_id}")
        return await get_budget_status(budget_id=budget_id, user_id=user_id)
    
    @staticmethod
    async def create_monthly_budget(
        user_id: int,
        name: str,
        amount: Decimal,
        year: int,
        month: int,
        category_id: Optional[int] = None,
        project_id: Optional[int] = None,
        currency: str = "USD"
    ) -> Optional[Budget]:
        """Create a budget for a specific month."""
        # Calculate date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        logger.info(f"Creating monthly budget for user {user_id}: {name}, {year}-{month}")
        return await create_budget(
            user_id=user_id,
            name=name,
            amount=amount,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            project_id=project_id,
            currency=currency
        )
    
    @staticmethod
    async def get_all_active_budgets_status(user_id: int) -> List[Dict[str, Any]]:
        """Get status for all active budgets for a user."""
        logger.info(f"Getting status for all active budgets for user {user_id}")
        
        # Get all active budgets
        budgets = await get_user_budgets(user_id=user_id, active_only=True)
        
        # Get status for each budget
        result = []
        for budget in budgets:
            status = await get_budget_status(budget_id=budget.id, user_id=user_id)
            if status:
                result.append(status)
                
        # Sort by percentage used (highest first)
        result.sort(key=lambda x: x["percent_used"], reverse=True)
        
        return result