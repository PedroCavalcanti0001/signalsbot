from colorama import init, Fore, Back                    
                    
totalEarnings=50
color=Fore.GREEN if totalEarnings > 0 else Fore.RED
print(Fore.BLUE + "\nLucro atual:",color + str(round(totalEarnings, 2)), Fore.RESET)