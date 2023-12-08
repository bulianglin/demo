import sys
import requests
import os
import json
import time

pool_token = ""
api_endpoint = "http://127.0.0.1:8181/<proxy_api_prefix>"

users_file = "users.txt"
session_tokens_file = "session_tokens.txt"
tokens_file = "tokens.txt"


def print_log(msg):
    print("[%s]%s"%((time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),msg))

def make_post_request(api_endpoint, endpoint_path, payload):
    url = f"{api_endpoint}{endpoint_path}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(url, headers=headers, data=payload)
        return response
    except Exception as e:
        print_log(str(e))
        return None

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        print_log(str(e))
        return []

def write_tokens(file_path, tokens):
    with open(file_path, 'w') as file:
        file.write('\n'.join(tokens))

def process_users(users_file, session_tokens_file):
    lines = read_file(users_file)
    if not lines:
        print_log(users_file + ": No users found. Exiting program.")
        return
        
    session_tokens = []
    for line in lines:
        username, password = line.split('----')
        payload = f'username={username}&password={password}'
        response = make_post_request(api_endpoint, "/api/auth/login", payload)
        
        if response.status_code == 200:
            token_info = response.json()
            session_tokens.append(token_info['session_token'])
            print_log(f"Success for {username}")
        else:
            print_log(f"Failed for {username}: {response.json().get('detail')}")
    
    write_tokens(session_tokens_file, session_tokens)
    print_log(f"Successfully extracted {len(session_tokens)} session tokens, Saved to file {session_tokens_file}")


def process_session_and_register(session_token):
    session_payload = f'session_token={session_token}'
    session_response = make_post_request(api_endpoint, "/api/auth/session", session_payload)

    if session_response.status_code != 200:
        print_log(f"Failed session token: {session_response.json().get('detail')}")
        return None

    session_info = session_response.json()
    access_token = session_info['access_token']
    
    #show_conversations=true&show_userinfo=true 默认不隔离会话，不隐藏账号信息
    register_payload = f'unique_name=pandora&access_token={access_token}&site_limit=&expires_in=0&show_conversations=true&show_userinfo=true' 
    register_response = make_post_request(api_endpoint, "/api/token/register", register_payload)

    if register_response.status_code != 200:
        print_log(f"Failed register: {register_response.json().get('detail')}")
        return None

    register_info = register_response.json()
    return {
        'share_token': register_info['token_key'],
        'expire_at': register_info['expire_at'],
        'session_token': session_info['session_token']
    }
    

def process_tokens(tokens_file, session_tokens_file):
    tokens = read_file(session_tokens_file)
    if not tokens:
        print_log(session_tokens_file + ": No tokens found. Exiting program.")
        return
    write_tokens(session_tokens_file + '_bak', tokens)
    
    share_tokens = []
    session_tokens = []
    token_expire_dict = {}
    for token in tokens:
        token_info = process_session_and_register(token)
        if token_info:
            token_expire_dict[token_info['expire_at']] = {token_info['share_token']: token_info['session_token']}
            share_tokens.append(token_info['share_token'])
            session_tokens.append(token_info['session_token'])
            print_log("Share Token:" + token_info['share_token'])

    global pool_token
    if share_tokens:
        share_token_str = '%0D%0A'.join(share_tokens)
        pool_payload = f'share_tokens={share_token_str}&pool_token={pool_token}'
        pool_response = make_post_request(api_endpoint, "/api/pool/update", pool_payload)
        if pool_response.status_code == 200:
            pool_info = pool_response.json()
            pool_token = pool_info['pool_token']
            print_log("Count:"+str(pool_info['count'])+" Pool Token:" + pool_token)
            
        write_tokens(tokens_file, share_tokens + [pool_token])
        print_log("Saved to file " + tokens_file)
        
    if session_tokens:
        write_tokens(session_tokens_file, session_tokens)
        print_log("Updated " + session_tokens_file)

    while True:
        current_time = int(time.time())
        min_expire_time = min(token_expire_dict.keys(), default=1)
        if min_expire_time == 1:
            print_log("No tokens found. Exiting program.")
            return

        if current_time > min_expire_time:
            tokens_dict = token_expire_dict.pop(min_expire_time)
            share_token = next(iter(tokens_dict))
            session_token = tokens_dict[share_token]
            if session_token in session_tokens:
                session_tokens.remove(session_token)
                    
            register_info = process_session_and_register(session_token)
            if register_info:
                print_log("Updated Share Token:"+ register_info['share_token'])
                token_expire_dict[register_info['expire_at']] = {register_info['share_token']: register_info['session_token']}
                session_tokens.append(register_info['session_token'])
            else:
                if share_token in share_tokens:
                    share_tokens.remove(share_token)
                    print_log("Expired. Deleted Share Token:"+ share_token)

                if share_tokens:
                    share_token_str = '%0D%0A'.join(share_tokens)
                    pool_payload = f'share_tokens={share_token_str}&pool_token={pool_token}'
                    pool_response = make_post_request(api_endpoint, "/api/pool/update", pool_payload)
                    if pool_response.status_code == 200:
                        pool_info = pool_response.json()
                        pool_token = pool_info['pool_token']
                        print_log("Updated Pool Token. Count:"+str(pool_info['count'])+" Pool Token:" + pool_token)
                    
                write_tokens(tokens_file, share_tokens + [pool_token])
                print_log("Updated " + tokens_file)


            write_tokens(session_tokens_file, session_tokens)
            print_log("Updated " + session_tokens_file)
                
        else:
            time_to_wait = min_expire_time - current_time + 2
            print_log("Next run at "+ time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + time_to_wait)))
            time.sleep(time_to_wait)

def get_argument_value(args, option, default=None):
    try:
        index = args.index(option)
        if index + 1 < len(args):
            return args[index + 1]
    except ValueError:
        pass
    return default

if __name__ == "__main__":
    users_file = get_argument_value(sys.argv, '-a', users_file)
    pool_token = get_argument_value(sys.argv, '-p', pool_token)

    if '-a' in sys.argv:
        process_users(users_file, session_tokens_file)
    else:
        process_tokens(tokens_file, session_tokens_file)