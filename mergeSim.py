import random
import math
from typing import List

FIELDS_PER_CASE: int = 100
FIELD_IS_BAD_IF_LTE: float = 0.025

learnedChanceFieldIsBad: float = 0.02


def apiCall(items: List[float]) -> bool:
    for item in items:
        if item <= FIELD_IS_BAD_IF_LTE:
            return False;
    return True;

# The one-at-a-time method
# This is silly because of course we know we'll need one call per field
# with this method, but simulating it anyway just because
# RETURNS [number of total API calls, number of fields successfully processed, number of individually identified bad fields]
def method_individual_calls(items: List[float]) -> tuple[int, int, int]:
    callCount: int = 0
    successCount: int = 0
    badFieldCount: int = 0    
    for i in range(0, len(items)):
        callCount += 1
        singleResult: bool = apiCall(items[i:i+1])
        if (singleResult):
            successCount += 1
        else:
            badFieldCount += 1
    return [ callCount, successCount, badFieldCount ]


# Split the list 50/50
# RETURNS [number of total API calls, number of fields successfully processed, number of individually identified bad fields]
def method_half_and_half(items: List[float]) -> tuple[int, int, int]:

    callCount: int = 0
    successCount: int = 0
    badFieldCount: int = 0
        
    # 0 = unknown, -1 = BAD, 1 = GOOD
    fieldStatus: List[int] = [-1] * len(items)
    halfway: int = math.floor(len(items)/2)
    partitions = [halfway, len(items)-halfway]

    # However we partitioned the list, run the process
    for p in range(len(partitions)):
        start = sum(partitions[0:p])
        end = start+partitions[p]
        thisGroup = items[start:end]

        # Count this API call
        callCount += 1
        result = apiCall(thisGroup)
        
        if not result:
            # A single, invalid field has been identified
            if (len(thisGroup) == 1):
                badFieldCount += 1
            else: 
                # recursively process the "bad" group that contains more than one field
                newResult =  method_half_and_half(thisGroup)
                callCount += newResult[0]
                successCount += newResult[1]
                badFieldCount += newResult[2]
        else:
            # Increment the number of new fields were successfully processed
            successCount = successCount + len(thisGroup)

    return [ callCount, successCount, badFieldCount ]

    
# Generate a case (which is a row containing the set number of fields)   
def new_case() -> List[float]:
    result: List[float] = []
    for i in range(0,FIELDS_PER_CASE):
        result.append(random.random())
    return result


def run_cases(total_tests: int):
    result_with_method_individual_calls: tuple[int, int, int] = [0, 0, 0]
    result_with_method_50_50: tuple[int, int, int] = [0, 0, 0]
    for i in range(total_tests):
        case = new_case()
        result_with_method_individual_calls = tuple(map(lambda i, j: i + j, result_with_method_individual_calls, method_individual_calls(case)))
        result_with_method_50_50 = tuple(map(lambda i, j: i + j, result_with_method_50_50, method_half_and_half(case)))

    print('API calls using method Individual Calls per field: ')
    print (result_with_method_individual_calls)
    print('Results result_with_50_50_method')
    print(result_with_method_50_50)
#  + str(total_calls_with_method_individual_calls)


total_tests_desired = int(input("How many tests should we run? "))

if (total_tests_desired > 1000000):
    print("Bah, humbug.I will not run more than 1 million tests.")
    total_tests_desired = 1000000

run_cases(total_tests_desired)
