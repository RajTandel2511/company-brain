"""Check transitive linked files for a job."""
import urllib.request, json, sys
r = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/api/jobs/19.50", timeout=30).read())
linked = r.get("linked_files", [])
print(f"Total linked files: {len(linked)}")
tag_counts = {}
for f in linked:
    tag_counts[f.get("primary_tag","?")] = tag_counts.get(f.get("primary_tag","?"), 0) + 1
print(f"By link reason: {tag_counts}")
print()
print("First 10:")
for f in linked[:10]:
    print(f"  [{f['primary_tag']:<10}] {f['name'][:60]:<60}  reasons={f['reasons'][:2]}")
