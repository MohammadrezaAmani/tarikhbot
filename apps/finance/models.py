from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from database.models import (
    User, Category, Transaction, Budget, Project,
    TransactionType
)

# Category-related functions
async def get_user_categories(
    user_id: int,
    transaction_type: Optional[TransactionType] = None
) -> List[Category]:
    """Get categories for a user, optionally filtered by transaction type."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    query = Category.filter(user=user)
    
    if transaction_type:
        query = query.filter(transaction_type=transaction_type)
    
    return await query.all()

async def create_category(
    user_id: int,
    name: str,
    transaction_type: Optional[TransactionType] = None,
    icon: Optional[str] = None,
    color: str = "#4A6FFF"
) -> Optional[Category]:
    """Create a new category."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None
    
    # Check if category already exists
    existing = await Category.filter(
        user=user,
        name=name,
        transaction_type=transaction_type
    ).first()
    
    if existing:
        return existing
    
    return await Category.create(
        user=user,
        name=name,
        transaction_type=transaction_type,
        icon=icon,
        color=color
    )

async def update_category(
    category_id: int,
    user_id: int,
    name: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None
) -> Optional[Category]:
    """Update a category."""
    try:
        user = await User.get(telegram_id=user_id)
        category = await Category.get(id=category_id, user=user)
    except DoesNotExist:
        return None
    
    if name is not None:
        category.name = name
    
    if transaction_type is not None:
        category.transaction_type = transaction_type
    
    if icon is not None:
        category.icon = icon
    
    if color is not None:
        category.color = color
    
    await category.save()
    return category

async def delete_category(category_id: int, user_id: int) -> bool:
    """Delete a category."""
    try:
        user = await User.get(telegram_id=user_id)
        category = await Category.get(id=category_id, user=user)
    except DoesNotExist:
        return False
    
    # Check if category is in use
    transaction_count = await Transaction.filter(category=category).count()
    if transaction_count > 0:
        # Don't delete categories that are in use
        return False
    
    await category.delete()
    return True

# Transaction-related functions
async def get_transaction(transaction_id: int, user_id: int) -> Optional[Transaction]:
    """Get a specific transaction."""
    try:
        user = await User.get(telegram_id=user_id)
        return await Transaction.get(id=transaction_id, user=user)
    except DoesNotExist:
        return None

async def get_user_transactions(
    user_id: int,
    transaction_type: Optional[TransactionType] = None,
    category_id: Optional[int] = None,
    project_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search_term: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Transaction]:
    """Get transactions for a user with various filters."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    # Start with base query
    query = Transaction.filter(user=user)
    
    # Apply filters
    if transaction_type:
        query = query.filter(type=transaction_type)
    
    if category_id:
        query = query.filter(category_id=category_id)
    
    if project_id:
        query = query.filter(project_id=project_id)
    
    if date_from:
        query = query.filter(date__gte=date_from)
    
    if date_to:
        query = query.filter(date__lte=date_to)
    
    if min_amount:
        query = query.filter(amount__gte=min_amount)
    
    if max_amount:
        query = query.filter(amount__lte=max_amount)
    
    if search_term:
        query = query.filter(
            Q(description__icontains=search_term) | 
            Q(category__name__icontains=search_term)
        )
    
    # Order by date (most recent first)
    return await query.order_by("-date", "-id").offset(offset).limit(limit).prefetch_related("category", "project")

async def create_transaction(
    user_id: int,
    amount: Decimal,
    transaction_type: TransactionType,
    date: date,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    project_id: Optional[int] = None,
    currency: str = "USD",
    is_recurring: bool = False,
    recurrence_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> Optional[Transaction]:
    """Create a new transaction."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None
    
    # Prepare transaction data
    transaction_data = {
        "user": user,
        "amount": amount,
        "type": transaction_type,
        "date": date,
        "description": description,
        "currency": currency,
        "is_recurring": is_recurring,
        "recurrence_data": recurrence_data,
        "metadata": metadata or {}
    }
    
    # Add category if provided
    if category_id:
        try:
            category = await Category.get(id=category_id)
            transaction_data["category"] = category
        except DoesNotExist:
            pass
    
    # Add project if provided
    if project_id:
        try:
            project = await Project.get(id=project_id)
            transaction_data["project"] = project
        except DoesNotExist:
            pass
    
    # Create the transaction
    return await Transaction.create(**transaction_data)

async def update_transaction(
    transaction_id: int,
    user_id: int,
    amount: Optional[Decimal] = None,
    transaction_type: Optional[TransactionType] = None,
    date: Optional[date] = None,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    project_id: Optional[int] = None,
    currency: Optional[str] = None,
    is_recurring: Optional[bool] = None,
    recurrence_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> Optional[Transaction]:
    """Update an existing transaction."""
    transaction = await get_transaction(transaction_id, user_id)
    if not transaction:
        return None
    
    # Update fields if provided
    if amount is not None:
        transaction.amount = amount
    
    if transaction_type is not None:
        transaction.type = transaction_type
    
    if date is not None:
        transaction.date = date
    
    if description is not None:
        transaction.description = description
    
    if currency is not None:
        transaction.currency = currency
    
    if is_recurring is not None:
        transaction.is_recurring = is_recurring
    
    if recurrence_data is not None:
        transaction.recurrence_data = recurrence_data
    
    if metadata is not None:
        # Merge with existing metadata
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata.update(metadata)
    
    if category_id is not None:
        try:
            if category_id == 0:  # Special case to remove category
                transaction.category = None
            else:
                category = await Category.get(id=category_id)
                transaction.category = category
        except DoesNotExist:
            pass
    
    if project_id is not None:
        try:
            if project_id == 0:  # Special case to remove project
                transaction.project = None
            else:
                project = await Project.get(id=project_id)
                transaction.project = project
        except DoesNotExist:
            pass
    
    # Save updated transaction
    await transaction.save()
    
    # Refresh to get updated relationships
    await transaction.fetch_related("category", "project")
    
    return transaction

async def delete_transaction(transaction_id: int, user_id: int) -> bool:
    """Delete a transaction."""
    transaction = await get_transaction(transaction_id, user_id)
    if not transaction:
        return False
    
    await transaction.delete()
    return True

# Budget-related functions
async def get_budget(budget_id: int, user_id: int) -> Optional[Budget]:
    """Get a specific budget."""
    try:
        user = await User.get(telegram_id=user_id)
        return await Budget.get(id=budget_id, user=user)
    except DoesNotExist:
        return None

async def get_user_budgets(
    user_id: int,
    active_only: bool = True,
    category_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> List[Budget]:
    """Get budgets for a user."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    query = Budget.filter(user=user)
    
    if active_only:
        today = date.today()
        query = query.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        )
    
    if category_id:
        query = query.filter(category_id=category_id)
    
    if project_id:
        query = query.filter(project_id=project_id)
    
    return await query.all()

async def create_budget(
    user_id: int,
    name: str,
    amount: Decimal,
    start_date: date,
    end_date: date,
    category_id: Optional[int] = None,
    project_id: Optional[int] = None,
    currency: str = "USD"
) -> Optional[Budget]:
    """Create a new budget."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return None
    
    # Prepare budget data
    budget_data = {
        "user": user,
        "name": name,
        "amount": amount,
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency
    }
    
    # Add category if provided
    if category_id:
        try:
            category = await Category.get(id=category_id)
            budget_data["category"] = category
        except DoesNotExist:
            pass
    
    # Add project if provided
    if project_id:
        try:
            project = await Project.get(id=project_id)
            budget_data["project"] = project
        except DoesNotExist:
            pass
    
    # Create the budget
    return await Budget.create(**budget_data)

async def update_budget(
    budget_id: int,
    user_id: int,
    name: Optional[str] = None,
    amount: Optional[Decimal] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    project_id: Optional[int] = None,
    currency: Optional[str] = None
) -> Optional[Budget]:
    """Update an existing budget."""
    budget = await get_budget(budget_id, user_id)
    if not budget:
        return None
    
    # Update fields if provided
    if name is not None:
        budget.name = name
    
    if amount is not None:
        budget.amount = amount
    
    if start_date is not None:
        budget.start_date = start_date
    
    if end_date is not None:
        budget.end_date = end_date
    
    if currency is not None:
        budget.currency = currency
    
    if category_id is not None:
        try:
            if category_id == 0:  # Special case to remove category
                budget.category = None
            else:
                category = await Category.get(id=category_id)
                budget.category = category
        except DoesNotExist:
            pass
    
    if project_id is not None:
        try:
            if project_id == 0:  # Special case to remove project
                budget.project = None
            else:
                project = await Project.get(id=project_id)
                budget.project = project
        except DoesNotExist:
            pass
    
    # Save updated budget
    await budget.save()
    
    return budget

async def delete_budget(budget_id: int, user_id: int) -> bool:
    """Delete a budget."""
    budget = await get_budget(budget_id, user_id)
    if not budget:
        return False
    
    await budget.delete()
    return True

async def get_budget_status(
    budget_id: int, 
    user_id: int
) -> Optional[Dict[str, Any]]:
    """Get status of a specific budget with spending details."""
    budget = await get_budget(budget_id, user_id)
    if not budget:
        return None
    
    # Build query for transactions in this budget's timeframe
    query = Transaction.filter(
        user_id=budget.user_id,
        date__gte=budget.start_date,
        date__lte=budget.end_date,
        type=TransactionType.EXPENSE  # Only count expenses
    )
    
    # Filter by category if budget is category-specific
    if budget.category_id:
        query = query.filter(category_id=budget.category_id)
    
    # Filter by project if budget is project-specific
    if budget.project_id:
        query = query.filter(project_id=budget.project_id)
    
    # Execute query and calculate total
    transactions = await query.all()
    spent_amount = sum(t.amount for t in transactions if t.currency == budget.currency)
    
    # Calculate percentage and remaining amount
    if budget.amount > 0:
        percent_used = (spent_amount / budget.amount) * 100
    else:
        percent_used = 0
    
    remaining_amount = budget.amount - spent_amount
    
    # Determine status
    if percent_used >= 100:
        status = "over_budget"
    elif percent_used >= 80:
        status = "warning"
    else:
        status = "good"
    
    return {
        "budget": budget,
        "spent_amount": spent_amount,
        "remaining_amount": remaining_amount,
        "percent_used": percent_used,
        "status": status,
        "transaction_count": len(transactions),
        "transactions": transactions[-5:],  # Return the 5 most recent transactions
    }

# Financial summary functions
async def get_expense_summary_by_category(
    user_id: int,
    date_from: date,
    date_to: date,
    currency: str = "USD"
) -> List[Dict[str, Any]]:
    """Get expense summary grouped by category."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return []
    
    # Get all expenses for the period
    transactions = await Transaction.filter(
        user=user,
        type=TransactionType.EXPENSE,
        date__gte=date_from,
        date__lte=date_to,
        currency=currency
    ).prefetch_related("category")
    
    # Group by category
    category_summary = {}
    for transaction in transactions:
        category_name = transaction.category.name if transaction.category else "Uncategorized"
        category_id = transaction.category_id or 0
        
        if category_id not in category_summary:
            category_summary[category_id] = {
                "category_id": category_id,
                "category_name": category_name,
                "amount": Decimal('0'),
                "count": 0,
                "color": transaction.category.color if transaction.category else "#CCCCCC"
            }
        
        category_summary[category_id]["amount"] += transaction.amount
        category_summary[category_id]["count"] += 1
    
    # Convert to list and sort by amount (highest first)
    result = list(category_summary.values())
    result.sort(key=lambda x: x["amount"], reverse=True)
    
    # Calculate total for percentages
    total_amount = sum(item["amount"] for item in result)
    if total_amount > 0:
        for item in result:
            item["percentage"] = (item["amount"] / total_amount) * 100
    else:
        for item in result:
            item["percentage"] = 0
    
    return result

async def get_monthly_summary(
    user_id: int,
    year: int,
    month: int,
    currency: str = "USD"
) -> Dict[str, Any]:
    """Get financial summary for a specific month."""
    try:
        user = await User.get(telegram_id=user_id)
    except DoesNotExist:
        return {
            "income": Decimal('0'),
            "expenses": Decimal('0'),
            "balance": Decimal('0'),
            "income_transactions": [],
            "expense_transactions": [],
            "expense_by_category": []
        }
    
    # Calculate date range for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get income transactions
    income_transactions = await Transaction.filter(
        user=user,
        type=TransactionType.INCOME,
        date__gte=start_date,
        date__lte=end_date,
        currency=currency
    ).prefetch_related("category", "project")
    
    # Get expense transactions
    expense_transactions = await Transaction.filter(
        user=user,
        type=TransactionType.EXPENSE,
        date__gte=start_date,
        date__lte=end_date,
        currency=currency
    ).prefetch_related("category", "project")
    
    # Calculate totals
    income_total = sum(t.amount for t in income_transactions)
    expense_total = sum(t.amount for t in expense_transactions)
    balance = income_total - expense_total
    
    # Get expense by category
    expense_by_category = await get_expense_summary_by_category(
        user_id=user_id,
        date_from=start_date,
        date_to=end_date,
        currency=currency
    )
    
    return {
        "income": income_total,
        "expenses": expense_total,
        "balance": balance,
        "income_transactions": income_transactions,
        "expense_transactions": expense_transactions,
        "expense_by_category": expense_by_category
    }