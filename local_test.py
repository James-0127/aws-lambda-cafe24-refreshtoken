from lambda_function import lambda_handler

def main():
    """
    Cafe24 redirect에서 받은 실제 code를 여기에 넣어 테스트할 수 있음.
    지금은 예시 값. 실제 유효 code로 바꿔서 테스트하면 진짜 Cafe24에 요청 가고 DB upsert까지 감.
    """

    event = {
        "queryStringParameters": {}
    }

    resp = lambda_handler(event, None)
    print("Lambda response:")
    print(resp["statusCode"])
    print(resp["body"])

if __name__ == "__main__":
    main()