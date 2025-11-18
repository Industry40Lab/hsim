"""
Test script for MethodIntrospector
"""

from hsim.gui.utils.method_introspector import MethodIntrospector

# Test with a Server block
print("=" * 60)
print("Testing MethodIntrospector with Server block")
print("=" * 60)

methods = MethodIntrospector.get_class_methods('server')

print(f"\nFound {len(methods)} methods:")
for method_name, method_info in sorted(methods.items()):
    print(f"\n  {method_name}")
    print(f"    Signature: {method_info['signature'][:80]}...")
    print(f"    Public: {method_info['is_public']}")
    if method_info['docstring']:
        print(f"    Doc: {method_info['docstring'][:60]}...")

# Test categorization
print("\n" + "=" * 60)
print("Method Categories")
print("=" * 60)

categories = MethodIntrospector.get_method_categories(methods)
for category, method_list in categories.items():
    print(f"\n{category}:")
    for method_name in method_list:
        print(f"  - {method_name}")

# Test with Generator
print("\n" + "=" * 60)
print("Testing with Generator block")
print("=" * 60)

gen_methods = MethodIntrospector.get_class_methods('generator')
print(f"\nFound {len(gen_methods)} methods for Generator")

# Test attributes
print("\n" + "=" * 60)
print("Testing Attributes")
print("=" * 60)

attributes = MethodIntrospector.get_class_attributes('server')
print(f"\nFound {len(attributes)} attributes:")
for attr_name, attr_info in sorted(attributes.items()):
    print(f"  {attr_name}: {attr_info['type']}")
