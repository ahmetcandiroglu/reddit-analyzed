# Implementation of SimRank algorithm for CS 425 Web-Scale Data Course Project
# The aim is to find similar subreddits based on users.

# This implementation works on a undirected graph where each subreddit is represented as a vertex
# and each weighted edge represents number of common users between subreddits.
# Users are not represented as vertices in this implementation for this reason this is much more faster.

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

# Get subreddit ids
sub_ids = database.get_sub_ids(conn)
num_subs = len(sub_ids)
print('Initialized sub_ids.')


# Initialize in_links and out_link_nums
# in_links is list of tuples of subreddit ids and number of common users i.e (sub_id, #common user)
t_start = time.time()

in_links = {}
out_link_nums = {}
for sub_id in sub_ids:
    in_links[sub_id] = database.get_sub_in_links_v2(conn, sub_id)
    out_link_num = 0
    for link in in_links[sub_id]:
        out_link_num += link[1]
    out_link_nums[sub_id] = out_link_num

    stdout.write(f"\rGet in_links and out_link_nums for {sub_id}/{num_subs}")
    stdout.flush()

elapsed_time = (time.time() - t_start)
print("\nInitializing in_links took %.2fsec\n" % elapsed_time)


# Run SimRank for each subreddit
t_start_all = time.time()

for sub_id in sub_ids:
    t_start = time.time()

    teleport_set = sub_id

    # Initialize r_old and r_new vectors
    # r_old and r_new vector hold PageRank value of each vertex (subreddit and user)
    r_old = {}
    r_new = {}
    for sub in sub_ids:
        r_old[sub] = float(0)
        r_new[sub] = float(1)

    # Do one iteration of matrix vector multiplication
    def update_r_new():
        # Update PageRank value of every vertex
        for vertex in sub_ids:
            vertex_in_links = in_links[vertex]
            sum_in = 0.0
            for in_link in vertex_in_links:
                in_sub_id, common_user_num = in_link
                sum_in += (beta * common_user_num * r_old[in_sub_id]) / (out_link_nums[in_sub_id])

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
    database.insert_sub_similarities(conn, teleport_set, r_new, limit=0.01)

    elapsed_time = (time.time() - t_start)
    stdout.write(f"\rCompleted {teleport_set}/{num_subs} in {round(elapsed_time, 2)}sec ({iter_count} iterations)")
    stdout.flush()


elapsed_time = (time.time() - t_start_all)
print("\nEverything took %.2fsec" % elapsed_time)
print("The end.")
