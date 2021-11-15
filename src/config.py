from pathlib import Path


class Config:

    @staticmethod
    def load_config():
        config = {}
        base_path = Path(__file__).parent
        file_path = (base_path / "../resources/config.txt").resolve()
        with open(file_path, encoding='utf8') as configFile:
            allLines = configFile.readlines()
            for line in allLines:
                split = line.split(":")
                if line.startswith("email"):
                    config["email"] = split[1].strip()
                elif line.startswith("password"):
                    config["password"] = split[1].strip()
                elif line.startswith("maxwin"):
                    config["maxwin"] = split[1].strip()
                elif line.startswith("operatingpercentage"):
                    config["operatingpercentage"] = split[1].strip()
                elif line.startswith("mode"):
                    config["mode"] = split[1].strip()
                elif line.startswith("galefactor"):
                    config["galefactor"] = split[1].strip()
                elif line.startswith("options"):
                    config["options"] = split[1].strip()
                elif line.startswith("respecttrend"):
                    config["respecttrend"] = split[1].strip()
                elif line.startswith("galemax"):
                    config["galemax"] = split[1].strip()
                elif line.startswith("delay"):
                    config["delay"] = split[1].strip()
        return config
