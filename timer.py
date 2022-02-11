import time

class timer:
    def __init__(self) -> None:                                     self.start_time = self.current_time()
    def current_time(self) -> float:                                return time.time()
    def restart(self) -> None:                                      self.start_time = self.current_time()
    def get_time_elapsed(self) -> float:                            return self.current_time() - self.start_time
    def get_time_elapsed_and_restart(self) -> float:
        result = self.get_time_elapsed()
        self.restart()
        return result
    #def get_formatted_time(self, time_to_format) -> str:            return time.strftime('%S' if time_to_format<60 else '%M:%S' if time_to_format<3600 else '%H:%M:%S', time.gmtime(time_to_format))
    def get_formatted_time_elapsed(self) -> str:                    return time.strftime('%H:%M:%S', time.gmtime(self.get_time_elapsed()))
    def get_formatted_time_elapsed_and_restart(self) -> str:        return time.strftime('%H:%M:%S', time.gmtime(self.get_time_elapsed_and_restart()))
    ...

if __name__ == "__main__":
    mytimer = timer()
    time.sleep(3)
    print(mytimer.get_time_elapsed())
    time.sleep(2)
    print(mytimer.get_time_elapsed_and_restart())
    time.sleep(1)
    print(mytimer.get_formatted_time_elapsed())
    time.sleep(2)
    print(mytimer.get_formatted_time_elapsed_and_restart())
    print("\n\tNO ERRORS FOUND :)\n")