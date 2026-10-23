
"""Library catalog management module.

Provides functions to issue and return books, check availability,
calculate fines, generate patron hashes and PINs, and export the catalog.
"""

import hashlib
import os
import secrets

catalog = {
    "B01": {"title": "Clean Code", "copies": 3},
    "B02": {"title": "The Pragmatic Programmer", "copies": 1},
    "B03": {"title": "Design Patterns", "copies": 2},
}


def issue_book(book_id, patron, active_issues=None):
    """Issue an available book to a patron."""
    if active_issues is None:
        active_issues = []

    if book_id not in catalog or catalog[book_id]["copies"] <= 0:
        return False

    catalog[book_id]["copies"] -= 1
    active_issues.append(f"Issued book {book_id} to patron {patron}")
    return True


def return_book(book_id):
    """Return a book to the catalog."""
    if book_id not in catalog:
        return False

    catalog[book_id]["copies"] += 1
    return True


def check_availability(book_id):
    """Check whether a book has available copies."""
    if book_id not in catalog:
        return False

    return catalog[book_id]["copies"] > 0


def calculate_fine(days_overdue, daily_rate=2.0):
    """Calculate a fine using the number of overdue days and daily rate."""
    if days_overdue < 0 or daily_rate < 0:
        raise ValueError("Days overdue and daily rate cannot be negative.")

    return days_overdue * daily_rate


def generate_patron_hash(patron_id):
    """Generate a SHA-256 hash for a patron ID."""
    return hashlib.sha256(patron_id.encode("utf-8")).hexdigest()


def generate_temp_patron_pin():
    """Generate a random four-digit patron PIN."""
    return secrets.randbelow(9000) + 1000


def export_catalog(filename="catalog_export.txt"):
    """Export the current catalog to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(str(catalog))

    print(f"Catalog backup exported to: {filename}")


def main():
    """Run a demonstration of the library catalog functions."""
    librarian_key = os.environ.get("LIBRARIAN_KEY")

    issue_book("B01", "P101")
    return_book("B02")

    print("Is B01 available:", check_availability("B01"))
    print("Fine accrued:", calculate_fine(4))
    print("Patron Hash:", generate_patron_hash("P101"))
    print("Temp PIN:", generate_temp_patron_pin())

    export_catalog()
    print("Librarian key configured:", librarian_key is not None)


if __name__ == "__main__":
    main()
