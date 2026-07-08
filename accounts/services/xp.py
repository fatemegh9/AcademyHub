def add_xp(user, amount, reason=""):
    user.xp += amount
    user.save(update_fields=['xp'])