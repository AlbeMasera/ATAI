from demo_bot import Agent


def main():
    username = "kindle-pizzicato-wheat_bot"
    password = "zJD7llj0A010Zg"

    # Connect endlessly to Speakeasy
    while True:
        try:
            demobot = Agent(username, password)
            demobot.listen()

        except Exception as e:
            print("Exception encountered:", e)

        except KeyboardInterrupt:
            print("Keyboard interrupt")
            return


if __name__ == "__main__":
    main()
