# Implementation of a basic database wrapper for CS 425 Web-Scale Data Course Project
# The aim is to abstract data reads and writes.

# You can implement your own module which does not depend on a database.


import pymysql
from pymysql import IntegrityError

import config


source_table = 'sub_authors'
minhash_output_table = 'common_users'
simrank_output_table = 'simrank_sims'

author_postfix = '0000'


def connect_db():
    return pymysql.connect(host=config.DB_HOST,
                           user=config.DB_USER,
                           password=config.DB_PASSWORD,
                           db=config.DB_NAME,
                           connect_timeout=6000)


def get_sub_ids(connection):
    cursor = connection.cursor()
    sql = f"SELECT DISTINCT(sub_id) FROM {source_table}"
    cursor.execute(sql)
    return [str(item[0]) for item in cursor.fetchall()]


def get_user_ids(connection):
    cursor = connection.cursor()
    sql = f"SELECT DISTINCT(sub_id) FROM {source_table}"
    cursor.execute(sql)
    return [str(item[0]) + author_postfix for item in cursor.fetchall()]


def get_sub_users(connection, sub_id):
    cursor = connection.cursor()
    sql = f"SELECT author_id FROM {source_table} WHERE sub_id = %s"
    cursor.execute(sql, sub_id)
    return [str(item[0]) for item in cursor.fetchall()]


def get_sub_in_links(connection, sub_id):
    cursor = connection.cursor()
    sql = f"SELECT author_id FROM {source_table} WHERE sub_id = %s"
    cursor.execute(sql, int(sub_id))
    return [str(item[0]) + author_postfix for item in cursor.fetchall()]


def get_sub_in_links_v2(connection, sub_id):
    cursor = connection.cursor()
    sql = f'SELECT sub2, sim FROM {minhash_output_table} WHERE sub1 = %s'

    cursor.execute(sql, int(sub_id))
    return [(str(item[0]), int(item[1])) for item in cursor.fetchall()]


def get_user_in_links(connection, user_id):
    cursor = connection.cursor()
    sql = f"SELECT sub_id FROM {source_table} WHERE author_id = %s"
    cursor.execute(sql, int(user_id))
    return [str(item[0]) for item in cursor.fetchall()]


def insert_common_user_nums(connection, sub_i, user_nums):
    cursor = connection.cursor()
    sql = f"INSERT INTO {minhash_output_table} (sub1, sub2, sim) VALUES (%s, %s, %s)"

    try:
        cursor.executemany(sql, [(sub_i, sub_j, user_nums[sub_j]) for sub_j in user_nums])
        connection.commit()
    except IntegrityError:
        pass


def insert_sub_similarities(connection, base_id, sims, limit=0.01):
    cursor = connection.cursor()
    sql = f"INSERT INTO {simrank_output_table} (sub1, sub2, sim) VALUES (%s, %s, %s)"
    cursor.executemany(sql, [(base_id, sub_id, sims[sub_id]) for sub_id in sims
                             if base_id != sub_id and sims[sub_id] > limit])
    connection.commit()
