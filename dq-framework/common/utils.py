from pyspark.sql.functions import col
from common.constants import VAR_ENTITY_ID
from common.custom_logger import *
#logger = getlogger()
import logging
logger = get_logger()

#Extracts the active execution plan from the provided DataFrame by filtering rows where
#'is_active' is "Y". Converts the filtered data into a list of tuples for further processing.
def get_active_execution_plans(execution_plan_with_rule_df):
    try:
        plan_list = [tuple(row) for row in execution_plan_with_rule_df.filter(execution_plan_with_rule_df.is_active == "Y").collect()]
        logger.info("[DQ_GET_ACTIVE_PLANS] Active execution plans fetched successfully from execution plan table.")
        return plan_list
    except Exception as e:
        logger.error(f"[DQ_GET_ACTIVE_PLANS] Exception occured in fetch_execution_plan(): {e}")

#Merges the execution plan DataFrame with the rules DataFrame using 'rule_id' as the key.
#Drops duplicate or unnecessary columns and orders the result by 'ep_id'.
def join_execution_plan_with_rules(execution_plan_df,rules_df):
    try:
        execution_plan_with_rules_df = execution_plan_df.join(rules_df.select("rule_id", "rule_name"), execution_plan_df.rule_id == rules_df.rule_id, "inner").drop(execution_plan_df.last_update_date).drop(rules_df.rule_id).orderBy("ep_id")
        logger.info(f"[DQ_JOIN_PLANS_AND_RULES] Execution plans and rules joined successfully for data quality processing.")
        return execution_plan_with_rules_df
    except Exception as e:
        logger.error(f"[DQ_JOIN_PLANS_AND_RULES] Exception occured in join_execution_plan_with_rules(): {e}")

# fetch path from entity master table path
def fetch_entity_path(entity_master_df, entity_id):
    try:
        # Filter the dataframe for the specific entity_id and select file_path
        result = entity_master_df.filter(col("entity_id") == entity_id).select("file_path").first()
        
        # If a result is found, return the file_path, otherwise return None
        if result:
            logger.info(f"File path found for entity_id: {entity_id}")
            return result["file_path"]
        else:
            logger.error(f"No file path found for entity_id: {entity_id}")
            logger.warning(f"No file path found for entity_id: {entity_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching file path for entity_id: {entity_id} - {e}")
        return None
    
def fetch_rules(execution_plan_df):
    try:
        # Fetch distinct rule_ids from the dataframe and collect as a list
        rule_list = execution_plan_df.select("rule_id").distinct().rdd.flatMap(lambda x: x).collect()

        if not rule_list:
            logger.error(f"Rules does not exists in execution_plan_df for entity_id={VAR_ENTITY_ID}")
            return []
        # Log success
        logger.info("Successfully fetched rule list.")
        return rule_list
    except Exception as e:
        # Log error if something goes wrong
        logger.error(f"Error fetching rule list: {e}")
        return []

def fetch_filtered_rules(rule_list,rule_master_df):
    try:
        # Filter the rule_master_df for the given list of rule_ids
        rule_master_filtered_df = rule_master_df.filter(rule_master_df["rule_id"].isin(rule_list))
        # Log success
        logger.info(f"Successfully filtered {len(rule_list)} rules.")
        return rule_master_filtered_df
    except Exception as e:
        # Log error if filtering fails
        logger.error(f"Error filtering rules: {e}")
        return None
