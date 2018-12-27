# Implementation of SimRank algorithm for CS 425 Web-Scale Data Course Project
# The aim is to find similar subreddits based on users.

# This implementation works on a bipartite graph where subreddits and users are represented as a vertex
# and edges represent the user is active (commented) in the subreddit.
# There cannot be an edge between two subreddits in this implementation.

# Note: I kept the data in a MySQL database and used database module to read/write to it.
# However, you can import your module instead of database module to use txt file or anything else.


import time
from sys import stdout

import numpy as np
import database


# Connect to the database
conn = database.connect_db()
print('Connected to the database.')


# SimRank algorithm constants
# Teleportation constant
beta = 0.8
# Convergence limit
eps = 1e-3
# Number of maximum iterations
max_iter = 100


# Get subreddit and user data
sub_ids = database.get_sub_ids(conn)
user_ids = database.get_user_ids(conn)
all_vertex_ids = sub_ids + user_ids

num_subs = len(sub_ids)
num_users = len(user_ids)
print('Initialized all_vertex_ids.')


# Initialize all_in_links and out_link_nums
# for subreddits: in_links is list of user ids who commented on that subreddit
# for users: in_links is list of subreddit ids which user has commented on
t_start = time.time()

all_in_links = {}
out_link_nums = {}
for sub in sub_ids:
    all_in_links[sub] = database.get_sub_in_links(conn, sub)
    out_link_nums[sub] = len(all_in_links[sub])
    stdout.write(f"\rGet in_links for {sub}/{num_subs}")
    stdout.flush()

for user in user_ids:
    all_in_links[user] = database.get_user_in_links(conn, user)
    out_link_nums[user] = len(all_in_links[user])
    stdout.write(f"\rGet in_links for {user}/{num_users}")
    stdout.flush()

elapsed_time = (time.time() - t_start)
print("\nInitializing all_in_links and out_link_nums took %.2fsec\n" % elapsed_time)


# Run SimRank for each subreddit
t_start_all = time.time()

for sub_id in sub_ids:
    t_start = time.time()

    teleport_set = sub_id

    # Initialize r_old and r_new vectors
    # r_old and r_new vector hold PageRank value of each vertex (subreddit and user)
    r_old = {}
    r_new = {}
    for node_id in all_vertex_ids:
        r_old[node_id] = float(0)
        r_new[node_id] = float(1)

    # Do one iteration of matrix vector multiplication
    def update_r_new():
        # Update PageRank value of every vertex
        for vertex in all_vertex_ids:
            in_links = all_in_links[vertex]
            sum_in = 0.0
            for inlink in in_links:
                sum_in += (beta * r_old[inlink]) / out_link_nums[inlink]

            # Add teleportation constant
            if vertex == teleport_set:
                sum_in += (1 - beta)

            r_new[vertex] = sum_in


    iter_count = 0
    for iteration in range(max_iter):
        # Return condition
        if np.allclose(list(r_new.values()), list(r_old.values()), atol=eps):
            iter_count = iteration
            break

        for key in r_new:
            r_old[key] = r_new[key]
        update_r_new()

    # Amplify the SimRank values
    # Assume SimRank value of sub_i should be 1 for calculation of SimRank for sub_i
    amplifier = 1 / r_new[teleport_set]
    for sub in sub_ids:
        r_new[sub] *= amplifier

    # Write results to the database
    database.insert_sub_similarities(conn, sub_ids, r_new, limit=0.01)

    elapsed_time = (time.time() - t_start)
    stdout.write(f"\rCompleted {teleport_set}/{num_subs} in {round(elapsed_time, 2)}sec ({iter_count} iterations)")
    stdout.flush()


elapsed_time = (time.time() - t_start_all)
print("\nEverything took %.2fsec" % elapsed_time)
print("The end.")
