import random
import math
from typing import List
from enum import Enum
import csv

FIELDS_PER_CASE: int = 100

STARTING_GUESS_CHANCE_FIELD_IS_BAD: float = 0.9


def apiCall(items: List[float], FIELD_IS_BAD_IF_LTE: float) -> bool:
    for item in items:
        if item <= FIELD_IS_BAD_IF_LTE:
            return False;
    return True;

# The one-at-a-time method
# This is silly because of course we know we'll need one call per field
# with this method, but simulating it anyway just because it validates the results of the other methods
# RETURNS [number of total API calls, number of fields successfully processed, number of individually identified bad fields]
def method_individual_calls(items: List[float], FIELD_IS_BAD_IF_LTE: float) -> tuple[int, int, int]:
    callCount: int = 0
    successCount: int = 0
    badFieldCount: int = 0    
    for i in range(0, len(items)):
        callCount += 1
        singleResult: bool = apiCall(items[i:i+1], FIELD_IS_BAD_IF_LTE)
        if (singleResult):
            successCount += 1
        else:
            badFieldCount += 1
    return [ callCount, successCount, badFieldCount ]




# An enum to name the partition algorithms
class PartitionMethod(Enum):
    ONE_BY_ONE = 1
    HALF_AND_HALF = 2
    TARGET_50_50_CHANCE_CALL_SUCCEEDS = 3


# Split the list into individual items
# API call succeeding
def partition_method_one_by_one(items: List[float]) -> List[int]:
    partitions = [1] * len(items)
    return partitions


# Split the list 50/50
def partition_method_half_and_half(items: List[float]) -> List[int]:
    halfway: int = math.floor(len(items)/2)
    partitions = [halfway, len(items)-halfway]
    return partitions


# Split the list such that we have as close as possible to a 50/50 chance of each
# API call succeeding
def partition_method_50pct_chance_of_success(items: List[float], chanceFieldIsBad: float = STARTING_GUESS_CHANCE_FIELD_IS_BAD) -> List[int]:

    # Group size is number of items in each group. It is an integer as close to 50/50 as possible, but not less than 1 item per group
    # So the 0.5 here is the targeted 50/50 chance
    # (note we also avoid div by zero here)
    groupSize: int = 1
    if (chanceFieldIsBad != 0):
        groupSize = max(math.floor(0.5/chanceFieldIsBad), 1)

    # Group count is number of groups.
    groupCount: int = math.floor(len(items) / groupSize)

    # The following can happen if we were going to end up with single-item groups. Just remove a group at the end.
    if (groupCount * groupSize) > len(items):
        groupCount -= 1
        
    rez: List[int] = [groupSize] * groupCount
    
    # If the partitions didn't add up exactly to the item length we will add the difference to an additional, final item
    # so, e.g., if we had 100 fields and the target was 33 records per field
    # we would have [33, 33, 33] and one left over,
    # so this makes it [33, 33, 33, 1] so all fields will be processed
    if sum(rez) < len(items):
        rez.append(len(items) - sum(rez))
        # rez[len(rez)-1] = rez[len(rez)-1] + (len(items) - sum(rez))

    # Uncomment to see how this is breaking down the group:
    # print(str(rez) + ' after chanceFieldIsBad: ' + str(chanceFieldIsBad) + ' - groupSize: ' + str(groupSize) + ' groupCount: '+str(groupCount) )
    
    return rez


# Uses the specified method to partition the group
# For example, a one-by-one partition of a 10-item list will be: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
# Whereas a 50-50 partition of the same list will be:            [5, 5]
def get_partitions(items: List[float], method: PartitionMethod, chanceFieldIsBad: float = 0.5):
    if method == PartitionMethod.ONE_BY_ONE:
        return partition_method_one_by_one(items)
    elif method == PartitionMethod.HALF_AND_HALF:
        return partition_method_half_and_half(items)
    elif method == PartitionMethod.TARGET_50_50_CHANCE_CALL_SUCCEEDS:
        return partition_method_50pct_chance_of_success(items, chanceFieldIsBad)
    raise Exception("Unknown PartitionMethod")


# This returns the next partition method to use
# It basically exists just because if you start with the method "TARGET_50_50_CHANCE_CALL_SUCCEEDS"
#   then after the first partition you need to switch to the HALF_AND_HALF method
def get_next_method(previousMethod: PartitionMethod):
    if previousMethod == PartitionMethod.TARGET_50_50_CHANCE_CALL_SUCCEEDS:
        return PartitionMethod.HALF_AND_HALF
    return previousMethod


# Split the list 50/50
# RETURNS [number of total API calls, number of fields successfully processed, number of individually identified bad fields]
def processRecord(items: List[float], method: PartitionMethod, FIELD_IS_BAD_IF_LTE: float, chanceFieldIsBad: float = 0.5) -> tuple[int, int, int]:

    callCount: int = 0
    successCount: int = 0
    badFieldCount: int = 0

    # Get the partition using the specified method
    partitions = get_partitions(items, method, chanceFieldIsBad)

    # Update the method to the method that should be used after the first run
    # (see notes for this function, above)
    method = get_next_method(method)

    # However we partitioned the list, run the process
    for p in range(len(partitions)):
        start = sum(partitions[0:p])
        end = start+partitions[p]
        thisGroup = items[start:end]

        # Count this API call
        callCount += 1
        result = apiCall(thisGroup, FIELD_IS_BAD_IF_LTE)
        
        if not result:
            # A single, invalid field has been identified
            if (len(thisGroup) == 1):
                badFieldCount += 1
            else: 
                # recursively process the "bad" group that contains more than one field
                newResult =  processRecord(thisGroup, method, FIELD_IS_BAD_IF_LTE, chanceFieldIsBad)
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

    # Format of results will be a list with seven columns:
    # 1. The name of the Method
    # 2. The percentage of fields that are invalid for this run
    # 3. The resulting api_calls_per_record, which we want to ultimately minimize
    # 4. Total trials
    # 5. Total API calls
    # 6. Fields updated
    # 7. Fields found invalid
    headers = ['Method','Pct Fields Invalid','API Calls per Record','Records Processed','Total API Calls','Fields updated','Fields invalid']
    
    resultSet: List[tuple[str, float, float, int, int, int, int]] = []

    # Start off at a 1% chance a field is bad
    fieldIsBadIfLTE = 0.01
    learnedChanceFieldIsBad = STARTING_GUESS_CHANCE_FIELD_IS_BAD

    # Increment for each trial by 1 percent each time
    INCREMENT_BAD_FIELD_PCT: float = 0.01

    while fieldIsBadIfLTE <= 1:

        print('Running '+ str(total_tests) +' trials for probability: ' + str(fieldIsBadIfLTE) + '...')

        # Reset the results 
        result_SIMPLE: tuple[int, int, int] = [0, 0, 0]
        result_ONE_BY_ONE: tuple[int, int, int] = [0, 0, 0]
        result_HALF_AND_HALF: tuple[int, int, int] = [0, 0, 0]
        result_TARGET_50_50: tuple[int, int, int] = [0, 0, 0]
    
        for i in range(total_tests):

            # Generate a single case (one row, with, e.g., 100 fields)
            case = new_case()
            
            # Double-check results with the simplified one-by-one method
            result_SIMPLE = tuple(map(lambda i, j: i + j, \
                result_SIMPLE, \
                method_individual_calls(case, fieldIsBadIfLTE)))

            # Validate the recursive process with a one-by-one partition
            result_ONE_BY_ONE = tuple(map(lambda i, j: i + j, \
                result_ONE_BY_ONE, \
                processRecord(case, PartitionMethod.ONE_BY_ONE, fieldIsBadIfLTE)))

            # Actual test: 50/50 partitions with recursion
            result_HALF_AND_HALF = tuple(map(lambda i, j: i + j, \
                result_HALF_AND_HALF, \
                processRecord(case, PartitionMethod.HALF_AND_HALF, fieldIsBadIfLTE)))

            # Actual test: target a 50-50 chance of success for each API call
            # (this uses the "learnedChanceFieldIsBad" value based on prior cases)
            result_TARGET_50_50 = tuple(map(lambda i, j: i + j, \
                result_TARGET_50_50, \
                processRecord(case, PartitionMethod.TARGET_50_50_CHANCE_CALL_SUCCEEDS, fieldIsBadIfLTE, learnedChanceFieldIsBad)))

            # Update the current learnedChanceFieldIsBad based on cases-thus-far
            #    this is the % chance a field is bad based on data processed thus-far
            learnedChanceFieldIsBad = result_TARGET_50_50[2] / (result_TARGET_50_50[2] + result_TARGET_50_50[1])

        # Add to the result set

        # SIMPLE is just used for validating the results
        # resultSet.append(['SIMPLE',       fieldIsBadIfLTE, result_SIMPLE[0]             / total_tests, total_tests, result_SIMPLE[0],       result_SIMPLE[1],       result_SIMPLE[2]])
        
        resultSet.append(['ONE_BY_ONE',   fieldIsBadIfLTE, round(result_ONE_BY_ONE[0]         / total_tests, 4), total_tests, result_ONE_BY_ONE[0],      result_ONE_BY_ONE[1],   result_ONE_BY_ONE[2]])
        resultSet.append(['NAIVE_BINARY', fieldIsBadIfLTE, round(result_HALF_AND_HALF[0]      / total_tests, 4), total_tests, result_HALF_AND_HALF[0],   result_HALF_AND_HALF[1],    result_HALF_AND_HALF[2]])
        resultSet.append(['SMART_BINARY', fieldIsBadIfLTE, round(result_TARGET_50_50[0]       / total_tests, 4), total_tests, result_TARGET_50_50[0],    result_TARGET_50_50[1],     result_TARGET_50_50[2]])

        # Increase the percentage of fields that are bad
        fieldIsBadIfLTE = round(fieldIsBadIfLTE + INCREMENT_BAD_FIELD_PCT, 5)

    with open('simulation_results.csv', 'w', newline='') as csvfile:
        myWriter = csv.writer(csvfile)
        myWriter.writerow(headers)
        for row in resultSet:
            myWriter.writerow(row)
            
        


total_tests_desired = int(input("How many tests should we run? "))

if (total_tests_desired > 1000000):
    print("Bah, humbug. I am hardly in the mood to run more than 1 million tests.")
    total_tests_desired = 1000000

run_cases(total_tests_desired)
