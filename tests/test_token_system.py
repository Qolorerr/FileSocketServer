from qhelper import app, SignUpIn


async def test_signup() -> None:
    test_client = app.test_client()
    response = await test_client.post("/signup", json=SignUpIn(login="Tester",
                                                               email="tester@test.com",
                                                               password="SecretPassword"))
    data = response.status_code
    assert data == 201
