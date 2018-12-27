# Implementation of MinHash algorithm for CS 425 Web-Scale Data Course Project
# The aim is to find number of common users of each subreddit.

# This implementation takes a subreddit list and user list for each subreddit.
# Then, using MinHash algorithm, outputs number of common users for each subreddit.
# i.e for sub_1 and sub_2 -> output (sub_1, sub_2, #common users)

# Note: I kept the data in a MySQL database and used database module to read/write to it.
# However, you can import your module instead of database module to use txt file or anything else.

# This is implemented with the help of following GitHub repository
# https://github.com/chrisjmccormick/MinHash


import random
import time
from sys import stdout

import database


# Connect to the database
conn = database.connect_db()
print('Connected to the database.')


# Get subreddit ids
sub_ids = database.get_sub_ids(conn)
num_subs = len(sub_ids)


# Load users of each subreddit
all_users = {}
user_counts = {}
for sub in sub_ids:
    all_users[sub] = database.get_sub_users(conn, sub)
    user_counts[sub] = len(all_users[sub])

    stdout.write(f"\rCollect users of {sub}/{num_subs}")
    stdout.flush()
print(f'\nCollected all users of all {num_subs} subreddits.')


# Generate random permutations of n numbers where each in [0, limit)
def get_random_permutation(n, limit):
    result = []

    while n > 0:
        random_index = random.randint(0, limit)

        while random_index in result:
            random_index = random.randint(0, limit)

        result.append(random_index)
        n -= 1

    return result


# Measure elapsed time
t_start = time.time()

# h(x) = (ax + b) % c where a,b,c constants and x is row number
# h(x) is a hash function to permutate rows in an easy way
# Result of h(x) is the place of x-th row in the next permutation

# c is a prime number bigger than the number of all users
# Calculate c on an online website and put manually for simplicity
num_perms = 100
num_users = 3000000
c = 3000017

# Generate a and b values for num_perms times
a = get_random_permutation(num_perms, c)
b = get_random_permutation(num_perms, c)


# Generate MinHash signatures for each subreddit
# Each signature has length of num_perms
# i-th digit of signature denotes first encountered 1 value in permutation i
signatures = {}
for sub in sub_ids:
    stdout.write(f"\rGenerate signatures of {sub}/{num_subs}")
    stdout.flush()

    sub_users = all_users[sub]
    signature = []

    for i in range(num_perms):

        # Initialize minHash value to max value + 1 (i.e infinity)
        minHash = c + 1

        # Check all rows (users) and find minimum value of user id
        for user in sub_users:
            currHash = (a[i] * int(user) + b[i]) % c

            if currHash < minHash:
                minHash = currHash

        signature.append(minHash)

    # Save signature value of sub
    signatures[sub] = signature

elapsed_time = (time.time() - t_start)
print("\nGenerating MinHash signatures took %.2fsec" % elapsed_time)


t_start = time.time()

# Calculate number of common users between each subreddit
# First we need to calculate Jaccard similarity comparing signatures
# Then we can calculate number of common users using Jaccard similarity and number of users of each subreddit

# Jaccard Similarity = j
# j = |A and B| / |A or B|
# j = |A and B| / (|A| + |B| - |A and B|)
# |A and B| = j * (|A| + |B|) / (1 + j) = #Common users of A and B subreddits


# Threshold of Jaccard Similarity
# You may want to increase it to reduce output size and filter out non-similar subreddits right away
threshold = 0
common_user_nums = {}

for sub_i in sub_ids:
    stdout.write(f"\rCalculate #common users for {i}/{num_subs}")
    stdout.flush()

    signature_i = signatures[sub_i]
    common_user_nums[sub_i] = {}
    for sub_j in sub_ids:

        if sub_i == sub_j:
            continue

        signature_j = signatures[sub_j]

        # Count number of same signature digits
        count = 0
        for k in range(num_perms):
            count += (signature_i[k] == signature_j[k])

        # Calculate Jaccard Similarity
        # Jaccard Similarity = #Same signature digits / #Signature digits
        j_sim = count / num_perms

        # Disregard similarities lower than threshold
        if j_sim < threshold:
            continue

        # Calculate #Common users
        common_user_nums[sub_i][sub_j] = j_sim * (user_counts[sub_i] + user_counts[sub_j]) / (1 + j_sim)

elapsed_time = (time.time() - t_start)
print("\nGenerating number of common users took %.2fsec" % elapsed_time)


t_start = time.time()

# Save the results
for sub_i in common_user_nums:
    stdout.write(f"\rSave number of common users for {sub_i}/{num_subs}")
    stdout.flush()

    common_users = common_user_nums[sub_i]
    database.insert_jaccard_sim(conn, sub_i, common_users)

elapsed_time = (time.time() - t_start)
print("\nSaving the results took %.2fsec" % elapsed_time)


conn.close()
print("The end.")
