def Check_whether_category_is_duplicated(member, value_from_input):
    """True, wenn der Member schon eine Kategorie mit diesem Namen hat (Gross-/Kleinschreibung egal)."""
    return member.attributes.filter(category__iexact=value_from_input).exists()
