class Visibility:
    PRIVATE = 0
    PROTECTED = 1
    PUBLIC = 2

    choices = [
        (PRIVATE, "Private - only managers and invited experts can see"),
        (PROTECTED, "Protected - only managers, invited experts and the report submitter can see"),  # private + the person reporting it can see
        (PUBLIC, "Public - everyone can see (when this report is made public)"),  # the public can see (on a public report)
    ]
