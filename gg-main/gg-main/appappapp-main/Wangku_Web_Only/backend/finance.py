def money(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    return f"RM {amount:,.2f}"


def number(value):
    try:
        amount = float(str(value).replace(",", "").strip())
        return amount if amount >= 0 else None
    except (TypeError, ValueError):
        return None


def goal_progress(saved, target):
    if target <= 0:
        return 0.0
    return min(max(saved / target, 0.0), 1.0)


def monthly_allowance(amount, frequency):
    return amount * 4.33 if frequency == "Weekly" else amount


def months_to_goal(price, saved, monthly_saving):
    remaining = max(price - saved, 0)
    return None if monthly_saving <= 0 else remaining / monthly_saving


def category_totals(transactions):
    totals = {}
    for transaction in transactions:
        category = transaction.get("category", "Other")
        amount = number(transaction.get("amount")) or 0
        totals[category] = totals.get(category, 0) + amount
    return totals


def coach_allocation(available):
    """A transparent starter split; the future coach service can replace this rule."""
    amount = max(float(available or 0), 0)
    return {
        "Savings goal": round(amount * 0.50, 2),
        "Flexible spend": round(amount * 0.30, 2),
        "Buffer": round(amount * 0.20, 2),
    }


def distribute_savings(goals, amount):
    """Split a contribution evenly across unfinished goals, preserving cents and caps."""
    updated = [dict(goal) for goal in goals]
    remaining_cents = int(round(max(float(amount or 0), 0) * 100))

    while remaining_cents > 0:
        eligible = []
        for index, goal in enumerate(updated):
            target_cents = int(round((number(goal.get("target")) or 0) * 100))
            saved_cents = int(round((number(goal.get("saved")) or 0) * 100))
            if target_cents > saved_cents:
                eligible.append((index, target_cents, saved_cents))
        if not eligible:
            break

        base, extra_cents = divmod(remaining_cents, len(eligible))
        if base == 0:
            for index, target_cents, saved_cents in eligible[:remaining_cents]:
                updated[index]["saved"] = (saved_cents + 1) / 100
            remaining_cents = 0
            break

        unallocated_cents = 0
        for rank, (index, target_cents, saved_cents) in enumerate(eligible):
            share = base + (1 if rank < extra_cents else 0)
            credited = min(share, target_cents - saved_cents)
            updated[index]["saved"] = (saved_cents + credited) / 100
            unallocated_cents += share - credited

        if unallocated_cents >= remaining_cents:
            break
        remaining_cents = unallocated_cents

    return updated, remaining_cents / 100
