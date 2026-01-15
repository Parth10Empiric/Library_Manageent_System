import os
import csv
import django

# REPLACE 'your_project_name' with the name of the folder containing settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management_system.settings')
django.setup()

# REPLACE 'your_app_name' with the name of your app folder
from book.models import Book, Author, Category

def run_import():
    file_path = 'data.csv'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle ForeignKeys (find existing or create new)
            author_obj, _ = Author.objects.get_or_create(name=row['authors'])
            category_obj, _ = Category.objects.get_or_create(name=row['categories'])

            # Create Book
            Book.objects.create(
                title=row['title'],
                author=author_obj,
                category=category_obj
            )
    print("Data imported successfully!")

if __name__ == "__main__":
    run_import()
