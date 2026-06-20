from flask import Flask, render_template, request, jsonify, session
from collections import deque
import os

app = Flask(__name__)

# Secret key for session management (keeps user logged in)
app.secret_key = "social_network_group9_secret"

# ============================================================
# DATA STRUCTURE 1: HASH TABLE
# ============================================================
# Stores all user profiles using key-value pairs
# Key   = user_id (unique)
# Value = user details (name, password, friends, requests)
# Time Complexity: O(1) average for insert, lookup, delete
# Space Complexity: O(n) where n = number of users
# ============================================================
hash_table = {}

# ============================================================
# DATA STRUCTURE 2: GRAPH (Adjacency List)
# ============================================================
# Represents the social network as an undirected graph
# Each user (node/vertex) maps to a list of friends (edges)
# Undirected = friendship goes both ways
# Time Complexity: O(1) to add node, O(1) to add edge
# Space Complexity: O(V + E) where V = users, E = friendships
# ============================================================
graph = {}


# ============================================================
# FUNCTION: ADD USER
# Adds new user to both Hash Table and Graph
# ============================================================
def add_user(user_id, name, password):
    # Add to Hash Table — O(1) operation
    hash_table[user_id] = {
        "id": user_id,
        "name": name,
        "password": password,
        "friends": [],
        "pending_requests": [],   # received requests
        "sent_requests": [],      # sent requests
        "bio": "Hey there! I am using ConnectU.",
        "avatar_color": get_avatar_color(user_id)
    }
    # Add to Graph as new node — O(1) operation
    graph[user_id] = []
    print(f"[HASH TABLE] User '{name}' added — O(1) insert")
    print(f"[GRAPH] Node created for '{name}'")


# ============================================================
# FUNCTION: GET AVATAR COLOR
# Assigns a consistent color to each user based on their ID
# ============================================================
def get_avatar_color(user_id):
    colors = [
        "#1877f2", "#42b72a", "#f02849",
        "#8b5cf6", "#f59e0b", "#06b6d4",
        "#ec4899", "#10b981"
    ]
    # Use hash to consistently assign same color to same user
    return colors[hash(user_id) % len(colors)]


# ============================================================
# FUNCTION: ADD FRIENDSHIP
# Creates undirected edge between two nodes in the Graph
# ============================================================
def add_friend(user1_id, user2_id):
    if user1_id in graph and user2_id in graph:
        if user2_id not in graph[user1_id]:
            # Add edge in BOTH directions — undirected graph
            graph[user1_id].append(user2_id)
            graph[user2_id].append(user1_id)
            # Update Hash Table friends list
            hash_table[user1_id]["friends"].append(user2_id)
            hash_table[user2_id]["friends"].append(user1_id)
            print(f"[GRAPH] Edge added: '{user1_id}' <-> '{user2_id}'")
            return True
    return False


# ============================================================
# FUNCTION: REMOVE FRIENDSHIP
# Removes edge between two nodes in the Graph
# ============================================================
def remove_friend(user1_id, user2_id):
    if user1_id in graph and user2_id in graph:
        if user2_id in graph[user1_id]:
            graph[user1_id].remove(user2_id)
            graph[user2_id].remove(user1_id)
            hash_table[user1_id]["friends"].remove(user2_id)
            hash_table[user2_id]["friends"].remove(user1_id)
            print(f"[GRAPH] Edge removed: '{user1_id}' <-> '{user2_id}'")
            return True
    return False


# ============================================================
# ALGORITHM 1: BFS — Friend Suggestions
# ============================================================
# Breadth-First Search traverses graph level by level
# Level 1 = direct friends (skip these)
# Level 2 = friends of friends (suggest these)
# Uses a Queue (deque) — FIFO data structure
# Time Complexity:  O(V + E)
# Space Complexity: O(V)
# ============================================================
def bfs_friend_suggestions(user_id):
    if user_id not in graph:
        return []

    # Get direct friends to exclude from suggestions
    direct_friends = set(graph[user_id])
    # Get sent requests to exclude already-requested users
    sent_requests = set(hash_table[user_id].get("sent_requests", []))

    # Initialize BFS
    queue = deque([user_id])
    visited = set([user_id])
    suggestions = []

    print(f"[BFS] Starting traversal from '{user_id}'")

    while queue:
        current = queue.popleft()

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

                # Suggest if not direct friend, not self,
                # and no pending request already sent
                if (neighbor not in direct_friends and
                        neighbor != user_id and
                        neighbor not in sent_requests):

                    # Count mutual friends
                    mutual = len(set(graph[neighbor]) & direct_friends)
                    suggestions.append({
                        "id": neighbor,
                        "name": hash_table[neighbor]["name"],
                        "mutual_friends": mutual,
                        "avatar_color": hash_table[neighbor]["avatar_color"]
                    })

    # Rank suggestions using Insertion Sort
    suggestions = insertion_sort(suggestions)
    print(f"[BFS] Found {len(suggestions)} suggestions — O(V+E)")
    return suggestions


# ============================================================
# ALGORITHM 2: INSERTION SORT — Rank Suggestions
# ============================================================
# Sorts friend suggestions by mutual friend count (descending)
# Builds sorted list one element at a time
# Time Complexity:  O(n²) worst, O(n) best
# Space Complexity: O(1) — in place
# ============================================================
def insertion_sort(suggestions):
    for i in range(1, len(suggestions)):
        current = suggestions[i]
        j = i - 1
        # Shift elements with fewer mutual friends to the right
        while j >= 0 and suggestions[j]["mutual_friends"] < current["mutual_friends"]:
            suggestions[j + 1] = suggestions[j]
            j -= 1
        suggestions[j + 1] = current
    print(f"[INSERTION SORT] Ranked {len(suggestions)} suggestions — O(n²)")
    return suggestions


# ============================================================
# FUN FEATURE: SIX DEGREES OF SEPARATION
# ============================================================
# Uses BFS to find the SHORTEST PATH between two users
# Shows exact chain of connections between them
# Based on the theory that any two people are connected
# by at most 6 degrees of separation
# Time Complexity: O(V + E)
# ============================================================
def six_degrees(start_id, end_id):
    if start_id not in graph or end_id not in graph:
        return None

    # BFS with path tracking
    queue = deque([[start_id]])
    visited = set([start_id])

    print(f"[BFS - SIX DEGREES] Finding path: '{start_id}' -> '{end_id}'")

    while queue:
        path = queue.popleft()
        current = path[-1]

        # Found the destination!
        if current == end_id:
            # Convert IDs to names for display
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
                queue.append(path + [neighbor])

    print(f"[BFS] No path found between '{start_id}' and '{end_id}'")
    return None


# ============================================================
# FUN FEATURE: FRIEND LEADERBOARD
# ============================================================
# Ranks all users by number of friends using Insertion Sort
# Shows who is the most popular user in the network
# ============================================================
def get_leaderboard():
    users = []
    for uid, data in hash_table.items():
        users.append({
            "id": uid,
            "name": data["name"],
            "friend_count": len(data["friends"]),
            "avatar_color": data["avatar_color"]
        })

    # Sort by friend count using Insertion Sort (descending)
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
# Calculates compatibility % between two users
# Based on mutual friends ratio
# ============================================================
def friendship_strength(user1_id, user2_id):
    if user1_id not in graph or user2_id not in graph:
        return 0

    friends1 = set(graph[user1_id])
    friends2 = set(graph[user2_id])

    if not friends1 and not friends2:
        return 0

    # Jaccard similarity — mutual / total unique friends
    mutual = len(friends1 & friends2)
    total = len(friends1 | friends2)

    if total == 0:
        return 0

    # Scale to percentage
    strength = round((mutual / total) * 100)
    print(f"[HASH TABLE] Friendship strength calculated — O(1) lookup")
    return strength


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# AUTH: Signup
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    user_id = data["user_id"].strip()
    name = data["name"].strip()
    password = data["password"].strip()

    if not user_id or not name or not password:
        return jsonify({"success": False, "message": "All fields required"})
    if user_id in hash_table:
        return jsonify({"success": False, "message": "User ID already exists"})

    add_user(user_id, name, password)
    session["user_id"] = user_id
    return jsonify({"success": True, "message": f"Welcome, {name}!", "user": hash_table[user_id]})


# AUTH: Login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user_id = data["user_id"].strip()
    password = data["password"].strip()

    # Hash Table O(1) lookup
    if user_id not in hash_table:
        return jsonify({"success": False, "message": "User not found"})
    if hash_table[user_id]["password"] != password:
        return jsonify({"success": False, "message": "Wrong password"})

    session["user_id"] = user_id
    print(f"[HASH TABLE] Login lookup for '{user_id}' — O(1)")
    return jsonify({"success": True, "message": f"Welcome back!", "user": hash_table[user_id]})


# AUTH: Logout
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# AUTH: Get current session user
@app.route("/me", methods=["GET"])
def get_me():
    user_id = session.get("user_id")
    if not user_id or user_id not in hash_table:
        return jsonify({"success": False})
    return jsonify({"success": True, "user": hash_table[user_id]})


# FRIENDS: Send friend request
@app.route("/send_request", methods=["POST"])
def send_request():
    data = request.json
    from_id = data["from_id"]
    to_id = data["to_id"]

    if from_id not in hash_table or to_id not in hash_table:
        return jsonify({"success": False, "message": "User not found"})
    if to_id in hash_table[from_id]["friends"]:
        return jsonify({"success": False, "message": "Already friends"})
    if to_id in hash_table[from_id]["sent_requests"]:
        return jsonify({"success": False, "message": "Request already sent"})

    hash_table[from_id]["sent_requests"].append(to_id)
    hash_table[to_id]["pending_requests"].append(from_id)
    return jsonify({"success": True, "message": f"Friend request sent!"})


# FRIENDS: Accept friend request
@app.route("/accept_request", methods=["POST"])
def accept_request():
    data = request.json
    user_id = data["user_id"]
    from_id = data["from_id"]

    if from_id in hash_table[user_id]["pending_requests"]:
        hash_table[user_id]["pending_requests"].remove(from_id)
        hash_table[from_id]["sent_requests"].remove(user_id)
        add_friend(user_id, from_id)
        return jsonify({"success": True, "message": "Friend request accepted!"})
    return jsonify({"success": False, "message": "No request found"})


# FRIENDS: Decline friend request
@app.route("/decline_request", methods=["POST"])
def decline_request():
    data = request.json
    user_id = data["user_id"]
    from_id = data["from_id"]

    if from_id in hash_table[user_id]["pending_requests"]:
        hash_table[user_id]["pending_requests"].remove(from_id)
        hash_table[from_id]["sent_requests"].remove(user_id)
        return jsonify({"success": True, "message": "Request declined"})
    return jsonify({"success": False, "message": "No request found"})


# FRIENDS: Remove friend
@app.route("/remove_friend", methods=["POST"])
def api_remove_friend():
    data = request.json
    result = remove_friend(data["user1_id"], data["user2_id"])
    if result:
        return jsonify({"success": True, "message": "Friend removed"})
    return jsonify({"success": False, "message": "Could not remove friend"})


# DATA: Get all users
@app.route("/users", methods=["GET"])
def get_users():
    users = []
    for uid, data in hash_table.items():
        users.append({
            "id": uid,
            "name": data["name"],
            "friend_count": len(data["friends"]),
            "avatar_color": data["avatar_color"],
            "bio": data["bio"]
        })
    return jsonify({"success": True, "users": users})


# DATA: Get user profile
@app.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    if user_id not in hash_table:
        return jsonify({"success": False, "message": "User not found"})
    print(f"[HASH TABLE] Profile lookup for '{user_id}' — O(1)")
    data = hash_table[user_id].copy()
    data.pop("password", None)  # Never send password to frontend
    # Resolve friend IDs to names
    data["friends_data"] = [
        {"id": fid, "name": hash_table[fid]["name"],
         "avatar_color": hash_table[fid]["avatar_color"]}
        for fid in data["friends"] if fid in hash_table
    ]
    return jsonify({"success": True, "user": data})


# DATA: Get friend suggestions (BFS)
@app.route("/suggestions/<user_id>", methods=["GET"])
def get_suggestions(user_id):
    suggestions = bfs_friend_suggestions(user_id)
    return jsonify({"success": True, "suggestions": suggestions})


# DATA: Get graph data for visualizer
@app.route("/graph_data", methods=["GET"])
def get_graph_data():
    nodes = []
    edges = []
    seen_edges = set()

    for uid, data in hash_table.items():
        nodes.append({
            "id": uid,
            "name": data["name"],
            "avatar_color": data["avatar_color"],
            "friend_count": len(data["friends"])
        })

    for uid in graph:
        for neighbor in graph[uid]:
            edge_key = tuple(sorted([uid, neighbor]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({"from": uid, "to": neighbor})

    return jsonify({"success": True, "nodes": nodes, "edges": edges})


# FUN: Six Degrees of Separation
@app.route("/six_degrees", methods=["POST"])
def api_six_degrees():
    data = request.json
    path = six_degrees(data["start_id"], data["end_id"])
    if path:
        return jsonify({
            "success": True,
            "path": path,
            "degrees": len(path) - 1
        })
    return jsonify({"success": False, "message": "No connection found!"})


# FUN: Leaderboard
@app.route("/leaderboard", methods=["GET"])
def api_leaderboard():
    board = get_leaderboard()
    return jsonify({"success": True, "leaderboard": board})


# FUN: Friendship Strength
@app.route("/strength", methods=["POST"])
def api_strength():
    data = request.json
    strength = friendship_strength(data["user1_id"], data["user2_id"])
    return jsonify({"success": True, "strength": strength})


# DATA: Update bio
@app.route("/update_bio", methods=["POST"])
def update_bio():
    data = request.json
    user_id = data["user_id"]
    if user_id in hash_table:
        hash_table[user_id]["bio"] = data["bio"]
        return jsonify({"success": True})
    return jsonify({"success": False})


# ============================================================
# SEED DATA — pre-loads some users for demo purposes
# ============================================================
def seed_data():
    add_user("harshvir", "Harshvir Singh", "pass123")
    add_user("allan", "Allan Mwangi", "pass123")
    add_user("omar", "Omar Sahra", "pass123")
    add_user("anthony", "Anthony Mutinda", "pass123")
    add_user("zuruel", "Zuruel Kamande", "pass123")
    add_user("olocho", "Olocho Daniel", "pass123")

    # Add some friendships for demo
    add_friend("harshvir", "allan")
    add_friend("harshvir", "omar")
    add_friend("allan", "anthony")
    add_friend("omar", "zuruel")
    add_friend("anthony", "olocho")
    add_friend("zuruel", "olocho")

    print("[SEED] Demo data loaded successfully!")


if __name__ == "__main__":
    seed_data()
    app.run(debug=True)