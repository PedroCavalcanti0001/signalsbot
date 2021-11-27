from datetime import datetime
from pathlib import Path


class Signals:

    @staticmethod
    def load():
        signals = []
        base_path = Path(__file__).parent
        file_path = (base_path / "../../resources/signals.txt").resolve()
        with open(file_path, encoding='utf8') as signalsFile:
            lines = signalsFile.readlines()
            for line in lines:
                if not line.startswith("#") and not len(line.strip()) == 0 and len(line.strip().split(",")) == 5:
                    split1 = line.split(',')
                    parity = split1[0]
                    dateTimeStr = split1[1]
                    dateTimeSplit = dateTimeStr.split(":")
                    dt = datetime(int(dateTimeSplit[2].strip()), int(dateTimeSplit[1].strip()),
                                           int(dateTimeSplit[0].strip()),
                                           int(dateTimeSplit[3].strip()), int(dateTimeSplit[4].strip()))
                    timeframe = split1[2]
                    gale = split1[3]
                    tipo = split1[4]
                    signals.append({
                        "parity": parity.strip().upper(),
                        "datetime": dt,
                        "timeframe": timeframe.strip(),
                        "martingale": gale.strip(),
                        "action": tipo.strip().upper()
                    })
        return signals