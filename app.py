from flask import Flask, render_template, request, jsonify, session
from collections import deque
import os
import json

app = Flask(__name__)
app.secret_key = "social_network_group9_secret"

# ============================================================
# DATA STRUCTURE 1: HASH TABLE
# ============================================================
# OMAR'S PART
# ============================================================
# A Hash Table stores data as key-value pairs.
# Key   = user_id (unique identifier e.g. "harshvir")
# Value = user details (name, password, friends etc.)
#
# Why Hash Table?
# - O(1) average time for insert, lookup, delete
# - No need to loop through all users to find one
# - Like a contacts app — type a name, get details instantly
#
# COLLISION HANDLING:
# Python's dictionary handles collisions internally using
# open addressing — when two keys hash to the same index,
# Python finds the next available slot automatically.
# This keeps average case at O(1) despite collisions.
# Worst case is O(n) when many collisions chain together.
#
# Time Complexity:  O(1) average, O(n) worst case
# Space Complexity: O(n) where n = number of users
# ============================================================
hash_table = {}

# ============================================================
# DATA STRUCTURE 2: GRAPH (Adjacency List)
# ============================================================
# HARSHVIR'S PART
# ============================================================
# A Graph represents relationships between users.
# Each user is a NODE (vertex).
# Each friendship is an EDGE connecting two nodes.
# We use an ADJACENCY LIST — each node stores its neighbors.
#
# Example:
#   graph = {
#       "harshvir": ["allan", "omar"],
#       "allan":    ["harshvir", "anthony"],
#       "omar":     ["harshvir", "zuruel"]
#   }
#
# Why Adjacency List over Adjacency Matrix?
# - Matrix uses O(V²) space — stores ALL possible connections
# - List uses O(V+E) space — only stores ACTUAL connections
# - Social networks are SPARSE — most users aren't friends
#   with everyone, so the list is much more efficient
#
# Why Undirected Graph?
# - Friendship goes both ways — if A friends B, B friends A
# - Every edge is added in BOTH directions
#
# Time Complexity:  O(1) add node, O(1) add edge
# Space Complexity: O(V + E)
# ============================================================
graph = {}

# ============================================================
# JSON PERSISTENCE
# ============================================================
# HARSHVIR'S PART
# ============================================================
# Saves and loads data from a JSON file so users
# are NOT lost when the app restarts.
# Without this, all data resets every time app.py stops.
#
# How it works:
# - save_data() → writes hash_table to data.json
# - load_data() → reads data.json back into hash_table
#                 AND rebuilds the graph from friends lists
# - Called every time data changes (signup, add friend etc.)
# ============================================================
DATA_FILE = "data.json"


def save_data():
    """
    Saves the Hash Table to a JSON file.
    Called every time data changes.
    Time Complexity: O(n) — must write all users
    """
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(hash_table, f, indent=2)
        print("[JSON] Data saved successfully")
    except Exception as e:
        print(f"[JSON] Save error: {e}")


def load_data():
    """
    Loads the Hash Table from JSON file on startup.
    Also rebuilds the Graph from saved friend data.
    Returns True if data loaded, False if no file exists.
    Time Complexity: O(n) — must read all users
    """
    global hash_table, graph

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                hash_table = json.load(f)

            # Rebuild Graph from loaded Hash Table
            # JSON only saves the Hash Table
            # so we reconstruct graph edges from friends lists
            graph = {}
            for user_id, data in hash_table.items():
                graph[user_id] = data.get("friends", [])

            print(f"[JSON] Loaded {len(hash_table)} users from file")
            return True
        except Exception as e:
            print(f"[JSON] Load error: {e}")
            return False
    return False


# ============================================================
# FUNCTION: GET AVATAR COLOR
# ============================================================
# HARSHVIR'S PART
# ============================================================
# Assigns a consistent color to each user based on their ID.
# Uses Python's hash() to convert the string to a number.
# % len(colors) keeps the number within the list range.
# Same user_id ALWAYS gets the same color — consistent UI.
# ============================================================
def get_avatar_color(user_id):
    colors = [
        "#1877f2", "#42b72a", "#f02849",
        "#8b5cf6", "#f59e0b", "#06b6d4",
        "#ec4899", "#10b981"
    ]
    # hash() converts string to number
    # % len(colors) keeps it within 0-7 range
    return colors[hash(user_id) % len(colors)]


# ============================================================
# FUNCTION: ADD USER
# ============================================================
# OMAR'S PART
# ============================================================
# Adds a new user to BOTH data structures:
# 1. Hash Table — stores the user profile (key-value pair)
# 2. Graph      — creates a new empty node for the user
#
# Parameters:
#   user_id  (str) — unique ID chosen by user
#   name     (str) — display name
#   password (str) — user's password
#
# Time Complexity: O(1) — single Hash Table insert + Graph node
# ============================================================
def add_user(user_id, name, password):
    # Step 1: INSERT into Hash Table — O(1) average
    # user_id is the KEY, the dictionary is the VALUE
    hash_table[user_id] = {
        "id": user_id,
        "name": name,
        "password": password,
        "friends": [],           # Empty friends list
        "pending_requests": [],  # Friend requests received
        "sent_requests": [],     # Friend requests sent
        "bio": "Hey there! I am using ConnectU.",
        "avatar_color": get_avatar_color(user_id)
    }

    # Step 2: ADD NODE to Graph — O(1)
    # Empty list means no friends/connections yet
    graph[user_id] = []

    # Step 3: Save to JSON so data persists after restart
    save_data()

    print(f"[HASH TABLE] User '{name}' added — O(1) insert")
    print(f"[GRAPH] Node created for '{name}'")


# ============================================================
# FUNCTION: ADD FRIENDSHIP
# ============================================================
# HARSHVIR'S PART
# ============================================================
# Creates a friendship (edge) between two users in the Graph.
# Since friendship is mutual, edge is added in BOTH directions
# (undirected graph).
# Also updates the Hash Table friends list for both users.
#
# Parameters:
#   user1_id, user2_id (str) — IDs of the two users
#
# Returns:
#   True  — friendship created successfully
#   False — one user not found OR already friends
#
# Time Complexity: O(1) — append to adjacency list
# ============================================================
def add_friend(user1_id, user2_id):
    # Step 1: Check both users exist in Graph
    if user1_id in graph and user2_id in graph:

        # Step 2: Check they're not already friends
        if user2_id not in graph[user1_id]:

            # Step 3: Add edge in BOTH directions — undirected
            graph[user1_id].append(user2_id)
            graph[user2_id].append(user1_id)

            # Step 4: Update Hash Table friends lists for both
            hash_table[user1_id]["friends"].append(user2_id)
            hash_table[user2_id]["friends"].append(user1_id)

            # Step 5: Save updated data to JSON
            save_data()

            print(f"[GRAPH] Edge added: '{user1_id}' <-> '{user2_id}'")
            return True

    return False


# ============================================================
# FUNCTION: REMOVE FRIENDSHIP
# ============================================================
# HARSHVIR'S PART
# ============================================================
# Removes friendship (edge) between two users.
# Must remove from BOTH sides — undirected graph.
# Also updates Hash Table friends lists.
#
# Time Complexity: O(E) — must find and remove edge from list
# ============================================================
def remove_friend(user1_id, user2_id):
    if user1_id in graph and user2_id in graph:
        if user2_id in graph[user1_id]:

            # Remove edge from BOTH directions
            graph[user1_id].remove(user2_id)
            graph[user2_id].remove(user1_id)

            # Update Hash Table
            hash_table[user1_id]["friends"].remove(user2_id)
            hash_table[user2_id]["friends"].remove(user1_id)

            # Save updated data
            save_data()

            print(f"[GRAPH] Edge removed: '{user1_id}' <-> '{user2_id}'")
            return True
    return False


# ============================================================
# ALGORITHM 1: BFS — Friend Suggestions
# ============================================================
# ALLAN'S PART
# ============================================================
# Breadth-First Search traverses the graph LEVEL BY LEVEL.
# Think of it like ripples in water — spreading outward.
#
# HOW IT WORKS:
#   Level 0 = starting user (you)
#   Level 1 = your direct friends — SKIP (already connected)
#   Level 2 = friends of friends — SUGGEST these!
#   Level 3+ = further connections — also suggest
#
# WHY BFS NOT DFS?
#   DFS goes deep into one branch first — might find longer paths
#   BFS guarantees shortest path — more relevant suggestions
#
# KEY DATA STRUCTURE INSIDE BFS:
#   Queue (deque) — FIFO: First In First Out
#   Ensures closest connections are processed first
#
# Time Complexity:  O(V + E)
#   V = number of users (vertices)
#   E = number of friendships (edges)
# Space Complexity: O(V) — visited set + queue
# ============================================================
def bfs_friend_suggestions(user_id):
    if user_id not in graph:
        return []

    # Get direct friends — we will SKIP these in suggestions
    direct_friends = set(graph[user_id])

    # Get already-sent requests — avoid duplicate suggestions
    sent_requests = set(hash_table[user_id].get("sent_requests", []))

    # ── BFS INITIALIZATION ──
    # Queue holds users to visit next (FIFO — First In First Out)
    queue = deque([user_id])

    # Visited set — prevents revisiting same node
    # Without this, BFS would loop forever
    visited = set([user_id])

    # Results list
    suggestions = []

    print(f"[BFS] Starting traversal from '{user_id}'")

    # ── BFS MAIN LOOP ──
    # Keep going until all reachable nodes are visited
    while queue:

        # Take the FIRST person from queue (FIFO)
        current = queue.popleft()

        # Look at ALL friends of current person
        for neighbor in graph[current]:

            # Only process unvisited users
            if neighbor not in visited:
                visited.add(neighbor)      # Mark as visited
                queue.append(neighbor)     # Add to queue for later

                # SUGGEST if:
                # 1. Not already a direct friend
                # 2. Not the user themselves
                # 3. No friend request already sent
                if (neighbor not in direct_friends and
                        neighbor != user_id and
                        neighbor not in sent_requests):

                    # Count mutual friends for ranking by Insertion Sort
                    mutual = len(set(graph[neighbor]) & direct_friends)

                    suggestions.append({
                        "id": neighbor,
                        "name": hash_table[neighbor]["name"],
                        "mutual_friends": mutual,
                        "avatar_color": hash_table[neighbor]["avatar_color"]
                    })

    # Rank suggestions using Insertion Sort (Olocho's part)
    suggestions = insertion_sort(suggestions)
    print(f"[BFS] Found {len(suggestions)} suggestions — O(V+E)")
    return suggestions


# ============================================================
# ALGORITHM 2: INSERTION SORT — Rank Suggestions
# ============================================================
# OLOCHO'S PART
# ============================================================
# Sorts friend suggestions by mutual friend count (descending)
# so the most relevant suggestions appear first.
#
# HOW IT WORKS:
#   Like sorting a hand of playing cards:
#   1. Pick up cards one by one (iterate from index 1)
#   2. Each card: compare with cards to its LEFT
#   3. Shift larger cards RIGHT to make space
#   4. Insert card in its correct position
#   5. Repeat until all cards are sorted
#
# WHY INSERTION SORT?
#   - Simple to implement and explain
#   - O(1) space — sorts in place, no extra memory
#   - Stable — preserves order of equal elements
#   - Efficient for small lists (suggestions are small)
#
# Time Complexity:
#   Best Case:    O(n)   — already sorted list
#   Average Case: O(n²)  — random order
#   Worst Case:   O(n²)  — reverse sorted
# Space Complexity: O(1) — in place, no extra memory
# ============================================================
def insertion_sort(suggestions):
    # Start from index 1 — first element is already "sorted"
    for i in range(1, len(suggestions)):

        # Store current element to be inserted
        current = suggestions[i]

        # Start comparing with element to the LEFT
        j = i - 1

        # Shift elements with FEWER mutual friends to the right
        # We want DESCENDING order (most mutual friends first)
        while j >= 0 and suggestions[j]["mutual_friends"] < current["mutual_friends"]:
            suggestions[j + 1] = suggestions[j]  # Shift right
            j -= 1                                # Move left pointer

        # Insert current in its correct sorted position
        suggestions[j + 1] = current

    print(f"[INSERTION SORT] Ranked {len(suggestions)} suggestions — O(n²)")
    return suggestions


# ============================================================
# FUN FEATURE: SIX DEGREES OF SEPARATION
# ============================================================
# ALLAN'S PART
# ============================================================
# Uses BFS to find the SHORTEST PATH between two users.
# Based on the theory that any two people on Earth are
# connected by at most 6 degrees of separation.
#
# Difference from regular BFS:
# - Instead of storing just nodes, we store FULL PATHS
# - When destination is found, return the complete path
#
# Example result: harshvir → allan → anthony → olocho
# Degrees: 3 (three steps between harshvir and olocho)
#
# Time Complexity: O(V + E) — same as regular BFS
# ============================================================
def six_degrees(start_id, end_id):
    if start_id not in graph or end_id not in graph:
        return None

    # BFS with PATH TRACKING
    # Queue stores PATHS (lists) not just node IDs
    queue = deque([[start_id]])
    visited = set([start_id])

    print(f"[BFS - SIX DEGREES] Finding path: '{start_id}' -> '{end_id}'")

    while queue:
        path = queue.popleft()   # Get current path
        current = path[-1]       # Last node = current position

        # FOUND the destination!
        if current == end_id:
            # Convert IDs to full user details for display
            named_path = []
            for uid in path:
                named_path.append({
                    "id": uid,
                    "name": hash_table[uid]["name"],
                    "avatar_color": hash_table[uid]["avatar_color"]
                })
            print(f"[BFS] Path found — {len(path)-1} degrees of separation")
            return named_path

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                # Extend path with new neighbor
                queue.append(path + [neighbor])

    print(f"[BFS] No path found between '{start_id}' and '{end_id}'")
    return None


# ============================================================
# FUN FEATURE: FRIEND LEADERBOARD
# ============================================================
# OLOCHO'S PART
# ============================================================
# Ranks ALL users by number of friends using Insertion Sort.
# Shows who is the most popular user in the network.
# Directly demonstrates Insertion Sort on a different dataset.
# ============================================================
def get_leaderboard():
    # Collect all users with friend counts from Hash Table
    users = []
    for uid, data in hash_table.items():
        users.append({
            "id": uid,
            "name": data["name"],
            "friend_count": len(data["friends"]),
            "avatar_color": data["avatar_color"]
        })

    # Sort by friend count DESCENDING using Insertion Sort
    for i in range(1, len(users)):
        current = users[i]
        j = i - 1
        while j >= 0 and users[j]["friend_count"] < current["friend_count"]:
            users[j + 1] = users[j]
            j -= 1
        users[j + 1] = current

    print(f"[INSERTION SORT] Leaderboard ranked — O(n²)")
    return users


# ============================================================
# FUN FEATURE: FRIENDSHIP STRENGTH METER
# ============================================================
# OLOCHO'S PART
# ============================================================
# Calculates compatibility percentage between two users
# based on their mutual friends using Jaccard Similarity.
#
# Formula: mutual friends / total unique friends * 100
# Example: A has friends [B,C,D], X has friends [C,D,E]
#   Mutual = {C, D} = 2
#   Total  = {B, C, D, E} = 4
#   Strength = 2/4 * 100 = 50%
#
# Time Complexity: O(1) — Hash Table lookups
# ============================================================
def friendship_strength(user1_id, user2_id):
    if user1_id not in graph or user2_id not in graph:
        return 0

    friends1 = set(graph[user1_id])
    friends2 = set(graph[user2_id])

    if not friends1 and not friends2:
        return 0

    # Jaccard Similarity
    mutual = len(friends1 & friends2)  # Intersection
    total = len(friends1 | friends2)   # Union

    if total == 0:
        return 0

    strength = round((mutual / total) * 100)
    print(f"[HASH TABLE] Friendship strength calculated — O(1) lookup")
    return strength


# ============================================================
# FLASK ROUTES
# ============================================================
# ANTHONY'S PART
# ============================================================
# Flask routes are the API endpoints that connect the
# JavaScript frontend to the Python backend DSA logic.
#
# How it works:
# 1. JavaScript sends fetch() request to a route URL
# 2. Flask receives it and calls the right Python function
# 3. Python runs the algorithm on Graph/Hash Table
# 4. Result is returned as JSON to JavaScript
# 5. JavaScript updates the UI
#
# HTTP Methods:
# GET  — retrieving data (read operations)
# POST — sending/modifying data (write operations)
# ============================================================


# Home page — serves the HTML file
@app.route("/")
def index():
    return render_template("index.html")


# ── AUTH ROUTES ──────────────────────────────────────────────

# SIGNUP — Creates new user account
# Adds to Hash Table + Graph node
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json           # Get JSON from JavaScript
    user_id = data["user_id"].strip()
    name = data["name"].strip()
    password = data["password"].strip()

    # Validate all fields filled
    if not user_id or not name or not password:
        return jsonify({"success": False, "message": "All fields required"})

    # Hash Table O(1) check — does user already exist?
    if user_id in hash_table:
        return jsonify({"success": False, "message": "User ID already exists"})

    # Add user to Hash Table + Graph
    add_user(user_id, name, password)

    # Store in session — remembers who is logged in
    session["user_id"] = user_id

    # Never send password back to frontend
    safe_user = {k: v for k, v in hash_table[user_id].items() if k != "password"}
    return jsonify({"success": True, "message": f"Welcome, {name}!", "user": safe_user})


# LOGIN — Authenticates existing user
# Uses Hash Table O(1) lookup
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user_id = data["user_id"].strip()
    password = data["password"].strip()

    # Hash Table LOOKUP — O(1) average
    # Direct key access — no looping through all users
    if user_id not in hash_table:
        return jsonify({"success": False, "message": "User not found"})

    # Check password — O(1) Hash Table access
    if hash_table[user_id]["password"] != password:
        return jsonify({"success": False, "message": "Wrong password"})

    session["user_id"] = user_id
    print(f"[HASH TABLE] Login lookup for '{user_id}' — O(1)")

    safe_user = {k: v for k, v in hash_table[user_id].items() if k != "password"}
    return jsonify({"success": True, "message": "Welcome back!", "user": safe_user})


# LOGOUT — Clears session
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# GET ME — Returns current logged-in user from session
@app.route("/me", methods=["GET"])
def get_me():
    user_id = session.get("user_id")
    if not user_id or user_id not in hash_table:
        return jsonify({"success": False})
    safe_user = {k: v for k, v in hash_table[user_id].items() if k != "password"}
    return jsonify({"success": True, "user": safe_user})


# ── FRIEND REQUEST ROUTES ─────────────────────────────────────

# SEND REQUEST — Adds request to both users' Hash Table entries
@app.route("/send_request", methods=["POST"])
def send_request():
    data = request.json
    from_id = data["from_id"]
    to_id = data["to_id"]

    # Validation
    if from_id not in hash_table or to_id not in hash_table:
        return jsonify({"success": False, "message": "User not found"})
    if to_id in hash_table[from_id]["friends"]:
        return jsonify({"success": False, "message": "Already friends"})
    if to_id in hash_table[from_id]["sent_requests"]:
        return jsonify({"success": False, "message": "Request already sent"})

    # Update Hash Table for BOTH users — O(1)
    hash_table[from_id]["sent_requests"].append(to_id)
    hash_table[to_id]["pending_requests"].append(from_id)

    # Save to JSON
    save_data()

    return jsonify({"success": True, "message": "Friend request sent!"})


# ACCEPT REQUEST — Removes request, creates Graph edge
@app.route("/accept_request", methods=["POST"])
def accept_request():
    data = request.json
    user_id = data["user_id"]
    from_id = data["from_id"]

    if from_id in hash_table[user_id]["pending_requests"]:
        # Remove from pending and sent lists
        hash_table[user_id]["pending_requests"].remove(from_id)
        hash_table[from_id]["sent_requests"].remove(user_id)

        # Create friendship — adds Graph edge in both directions
        add_friend(user_id, from_id)

        # save_data() already called inside add_friend()
        return jsonify({"success": True, "message": "Friend request accepted!"})

    return jsonify({"success": False, "message": "No request found"})


# DECLINE REQUEST — Removes request, no Graph edge created
@app.route("/decline_request", methods=["POST"])
def decline_request():
    data = request.json
    user_id = data["user_id"]
    from_id = data["from_id"]

    if from_id in hash_table[user_id]["pending_requests"]:
        hash_table[user_id]["pending_requests"].remove(from_id)
        hash_table[from_id]["sent_requests"].remove(user_id)

        # Save updated data
        save_data()

        return jsonify({"success": True, "message": "Request declined"})

    return jsonify({"success": False, "message": "No request found"})


# REMOVE FRIEND — Deletes Graph edge between two users
@app.route("/remove_friend", methods=["POST"])
def api_remove_friend():
    data = request.json
    result = remove_friend(data["user1_id"], data["user2_id"])
    if result:
        return jsonify({"success": True, "message": "Friend removed"})
    return jsonify({"success": False, "message": "Could not remove friend"})


# ── DATA ROUTES ───────────────────────────────────────────────

# GET ALL USERS — Returns all users from Hash Table
@app.route("/users", methods=["GET"])
def get_users():
    users = []
    # Iterate through Hash Table — O(n)
    for uid, data in hash_table.items():
        users.append({
            "id": uid,
            "name": data["name"],
            "friend_count": len(data["friends"]),
            "avatar_color": data["avatar_color"],
            "bio": data["bio"]
        })
    return jsonify({"success": True, "users": users})


# GET USER PROFILE — Hash Table O(1) lookup by user_id
@app.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    # Hash Table O(1) lookup — direct key access
    if user_id not in hash_table:
        return jsonify({"success": False, "message": "User not found"})

    print(f"[HASH TABLE] Profile lookup for '{user_id}' — O(1)")

    data = hash_table[user_id].copy()
    data.pop("password", None)  # Never send password to frontend

    # Resolve friend IDs to full details
    data["friends_data"] = [
        {
            "id": fid,
            "name": hash_table[fid]["name"],
            "avatar_color": hash_table[fid]["avatar_color"]
        }
        for fid in data["friends"] if fid in hash_table
    ]
    return jsonify({"success": True, "user": data})


# GET SUGGESTIONS — Runs BFS algorithm
@app.route("/suggestions/<user_id>", methods=["GET"])
def get_suggestions(user_id):
    # BFS runs here — O(V+E)
    suggestions = bfs_friend_suggestions(user_id)
    return jsonify({"success": True, "suggestions": suggestions})


# GET GRAPH DATA — Returns nodes + edges for Network Visualizer
@app.route("/graph_data", methods=["GET"])
def get_graph_data():
    nodes = []
    edges = []
    seen_edges = set()  # Prevents duplicate edges (A->B and B->A)

    # Collect nodes from Hash Table
    for uid, data in hash_table.items():
        nodes.append({
            "id": uid,
            "name": data["name"],
            "avatar_color": data["avatar_color"],
            "friend_count": len(data["friends"])
        })

    # Collect edges from Graph
    for uid in graph:
        for neighbor in graph[uid]:
            # Sort edge key to avoid duplicates
            edge_key = tuple(sorted([uid, neighbor]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({"from": uid, "to": neighbor})

    return jsonify({"success": True, "nodes": nodes, "edges": edges})


# ── FUN FEATURE ROUTES ────────────────────────────────────────

# SIX DEGREES — Runs BFS path finding
@app.route("/six_degrees", methods=["POST"])
def api_six_degrees():
    data = request.json
    path = six_degrees(data["start_id"], data["end_id"])
    if path:
        return jsonify({"success": True, "path": path, "degrees": len(path) - 1})
    return jsonify({"success": False, "message": "No connection found!"})


# LEADERBOARD — Runs Insertion Sort on all users
@app.route("/leaderboard", methods=["GET"])
def api_leaderboard():
    board = get_leaderboard()
    return jsonify({"success": True, "leaderboard": board})


# STRENGTH — Calculates Jaccard similarity
@app.route("/strength", methods=["POST"])
def api_strength():
    data = request.json
    strength = friendship_strength(data["user1_id"], data["user2_id"])
    return jsonify({"success": True, "strength": strength})


# UPDATE BIO — Updates user bio in Hash Table
@app.route("/update_bio", methods=["POST"])
def update_bio():
    data = request.json
    user_id = data["user_id"]
    if user_id in hash_table:
        hash_table[user_id]["bio"] = data["bio"]
        save_data()  # Save updated bio
        return jsonify({"success": True})
    return jsonify({"success": False})


# ============================================================
# SEED DATA
# ============================================================
# HARSHVIR'S PART
# ============================================================
# Pre-loads 6 demo users with friendships for demonstration.
# Only runs if NO saved data.json file exists.
# This way real users created during demo are never overwritten.
# ============================================================
def seed_data():
    add_user("harshvir", "Harshvir Singh", "pass123")
    add_user("allan", "Allan Mwangi", "pass123")
    add_user("omar", "Omar Sahra", "pass123")
    add_user("anthony", "Anthony Mutinda", "pass123")
    add_user("zuruel", "Zuruel Kamande", "pass123")
    add_user("olocho", "Olocho Daniel", "pass123")

    # Add friendships — creates Graph edges
    add_friend("harshvir", "allan")
    add_friend("harshvir", "omar")
    add_friend("allan", "anthony")
    add_friend("omar", "zuruel")
    add_friend("anthony", "olocho")
    add_friend("zuruel", "olocho")

    print("[SEED] Demo data loaded successfully!")


# ============================================================
# APP STARTUP
# ============================================================
if __name__ == "__main__":
    # Try to load saved data first
    # If no saved data exists, load fresh seed data
    if not load_data():
        print("[STARTUP] No saved data — loading seed data")
        seed_data()
    else:
        print(f"[STARTUP] Loaded {len(hash_table)} existing users")

    app.run(debug=True)