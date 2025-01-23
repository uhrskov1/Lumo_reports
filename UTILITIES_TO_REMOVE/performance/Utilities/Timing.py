"""
========================================================================================================================================================================
-- Author:		Nicolai Henriksen
-- Create date: 2022-10-17
-- Description:	Decorator function for tracking bottlenecks
========================================================================================================================================================================
"""

import time


def PerformanceTracker(debug: bool = False):
    def PerformanceTrackerInner(func):
        def TimingFunction(*args, **kwargs):
            if debug:
                Time_Start = time.time()
                Result = func(*args, **kwargs)
                Time_End = time.time()
                totalTime = int((Time_End - Time_Start) * 1000)
                # TODO: Implement Log Function and PerformanceTracker
                print("%r  %2.2f ms" % (func.__name__, totalTime))
            else:
                Result = func(*args, **kwargs)
            return Result

        return TimingFunction

    return PerformanceTrackerInner
