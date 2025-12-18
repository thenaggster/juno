import json
from datetime import datetime, timedelta
import re

# Overall Health Status mapping
STATUS_SEVERITY = {
    "Red": 4,
    "Amber": 3,
    "Yellow": 2,
    "Green": 1,
    "Grey": 0,
    None: 0
}

# Priority mapping
PRIORITY_MULTIPLIER = {
    "Highest": 1.5,
    "High": 1.25,
    "Medium": 1.0,
    "Normal": 1.0,
    "Low": 0.75,
    "Lowest": 0.5,
    "Undefined": 1.0,
    None: 1.0
}

class Issue:
    def __init__(self, issue_data):
        self.key = issue_data.get("key")
        fields = issue_data.get("fields", {})
        self.summary = fields.get("summary", "")
        self.description = fields.get("description", "")
        self.comments = [comment.get("body", "") for comment in fields.get("comment", {}).get("comments", [])]
        self.created = datetime.strptime(fields.get("created").split(".")[0], "%Y-%m-%dT%H:%M:%S")
        self.priority = fields.get("priority", {}).get("name")
        self.status = fields.get("status", {}).get("name")
        self.issue_type = fields.get("issuetype", {}).get("name")
        
        self.status_summary = fields.get("customfield_12320841")
        self.rag_status = fields.get("customfield_12320845", {}).get("value")
        self.target_end_date_str = fields.get("customfield_12313942")
        self.target_end_date = datetime.strptime(self.target_end_date_str, "%Y-%m-%d") if self.target_end_date_str else None

        # Calculated fields
        self.weeks_active = 0
        self.status_contribution = 0
        self.computed_status_summary = ""
        self.text_sentiment = 0 
        self.computed_delivery_date = None
        self.computed_color_status = "Grey"

        # Roll-up fields
        self.status_summary_roll_up = ""
        self.overall_sentiment_score = 0
        self.parent = None
        self.children = []

    def calculate_weeks_active(self, current_date):
        self.weeks_active = (current_date - self.created).days / 7
    
    def calculate_status_contribution(self):
        #  It is calculated as 1 + (the number of children / 100).
        self.status_contribution = 1 + (len(self.children) / 100)

    def calculate_computed_status_summary(self):
        if self.status_summary:
            self.computed_status_summary = self.status_summary
        else:
            # Basic summary for now, can be improved with NLP
            texts = [self.summary, self.description] + self.comments
            self.computed_status_summary = ". ".join(filter(None, texts))

    def calculate_text_sentiment(self):
        positive_words = {"good", "great", "excellent", "resolved", "completed", "successful", "supportive", "achieved", "impressed"}
        negative_words = {"bad", "terrible", "poor", "unresolved", "blocked", "failed", "unsuccessful", "frustrated", "concerned", "issue", "problem", "blocker"}

        text_to_analyze = (self.summary + " " + self.description + " " + " ".join(self.comments)).lower()
        
        score = 0
        for word in text_to_analyze.split():
            if word in positive_words:
                score += 1
            elif word in negative_words:
                score -= 1
        self.text_sentiment = score

    def calculate_computed_delivery_date(self, current_date, open_descendants, velocity):
        if velocity > 0:
            days_to_complete = (open_descendants / velocity) * 7
            self.computed_delivery_date = current_date + timedelta(days=days_to_complete)

    def calculate_computed_color_status(self):
        if self.text_sentiment < -2:
            self.computed_color_status = "Red"
        elif self.computed_delivery_date and self.target_end_date:
            if self.computed_delivery_date > self.target_end_date:
                self.computed_color_status = "Red"
            elif (self.target_end_date - self.computed_delivery_date).days < 14:
                self.computed_color_status = "Amber"
            else:
                self.computed_color_status = "Green"
        elif self.text_sentiment < 0:
            self.computed_color_status = "Amber"
        else:
            self.computed_color_status = "Green"

def perform_roll_ups(issue):
    if not issue.children:
        issue.status_summary_roll_up = issue.computed_status_summary
        issue.overall_sentiment_score = issue.text_sentiment * PRIORITY_MULTIPLIER.get(issue.priority, 1.0) * issue.status_contribution
        return

    most_severe_status = "Grey"
    child_summaries = []
    sentiment_scores = []
    
    for child in issue.children:
        perform_roll_ups(child)
        
        if STATUS_SEVERITY.get(child.computed_color_status, 0) > STATUS_SEVERITY.get(most_severe_status, 0):
            most_severe_status = child.computed_color_status
        
        child_summaries.append(child.status_summary_roll_up)
        sentiment_scores.append(child.overall_sentiment_score)

    issue.computed_color_status = most_severe_status # Parent's health is the worst of its children
    issue.status_summary_roll_up = ". ".join([issue.computed_status_summary] + child_summaries)
    
    # Weighted average of sentiment scores
    if sentiment_scores:
        issue.overall_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
    else:
        issue.overall_sentiment_score = issue.text_sentiment * PRIORITY_MULTIPLIER.get(issue.priority, 1.0) * issue.status_contribution


def generate_markdown_report(root_issue, velocity, open_descendants, total_descendants):
    report = f"""
# Status Analysis for {root_issue.key}

## Overall Health Status: {root_issue.computed_color_status}

**Date of Analysis:** {datetime.now().strftime("%Y-%m-%d")}

---

## Health Analysis

**Computed Delivery Date:** {root_issue.computed_delivery_date.strftime("%Y-%m-%d") if root_issue.computed_delivery_date else "N/A"}
**Target End Date:** {root_issue.target_end_date.strftime("%Y-%m-%d") if root_issue.target_end_date else "N/A"}

**Analysis:**
The projected delivery date is based on the current velocity and number of open issues. The health status reflects whether the project is on track to meet its target end date.

---

## Sentiment Analysis

**Overall Sentiment Score:** {root_issue.overall_sentiment_score:.2f}

**Analysis:**
The sentiment score is a weighted average based on the sentiment of individual issues, their priority, and their contribution to the overall project. A higher score indicates a more positive sentiment.

---

## Detailed Breakdown

| Issue Key | Summary | Type | Status | Computed Status | Sentiment |
|---|---|---|---|---|---|
"""
    
    q = [root_issue]
    while q:
        issue = q.pop(0)
        report += f"| {issue.key} | {issue.summary} | {issue.issue_type} | {issue.status} | {issue.computed_color_status} | {issue.text_sentiment} |\n"
        for child in issue.children:
            q.append(child)
            
    return report


def get_oldest_resolution_date(jira_data):
    oldest_date = None
    for issue_data in jira_data.get("issues", []):
        fields = issue_data.get("fields", {})
        resolution_date_str = fields.get("resolutiondate")
        if resolution_date_str:
            resolution_date = datetime.strptime(resolution_date_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            if oldest_date is None or resolution_date < oldest_date:
                oldest_date = resolution_date
    return oldest_date

def calculate_issue_completion_velocity(total_descendants, oldest_resolution_date, current_date):
    if oldest_resolution_date is None:
        return 0
    weeks_since_first_resolution = (current_date - oldest_resolution_date).days / 7
    if weeks_since_first_resolution <= 0:
        return total_descendants # Avoid division by zero or negative weeks
    return total_descendants / weeks_since_first_resolution

def parse_jira_issues(jira_data):
    issues = {}
    for issue_data in jira_data.get("issues", []):
        issue = Issue(issue_data)
        issues[issue.key] = issue

    # Basic parent-child relationship, this will need to be improved
    # based on issue links or other hierarchy indicators.
    for issue in issues.values():
        parent_key_search = re.search(r"parent = (\w+-\d+)", issue.summary + issue.description)
        if parent_key_search:
            parent_key = parent_key_search.group(1)
            if parent_key in issues:
                issue.parent = issues[parent_key]
                issues[parent_key].children.append(issue)

    return issues

def main():
    # In a real scenario, this would be the live fetched data.
    # For now, I'll assume the data from the last tool call is available.
    # I will add the content later
    jira_data_str = """
    PASTE JIRA DATA HERE
    """
    
    # This is a placeholder. In the real script, I would not load from a string, 
    # but from the result of the `jira_search` tool call.
    try:
        jira_data = json.loads(jira_data_str)
        all_issues_data = json.loads(jira_data_str) # Assuming this contains all issues for velocity calc
        resolved_issues_data = json.loads(jira_data_str) # Assuming this contains resolved issues for oldest date
    except json.JSONDecodeError:
        jira_data = {"issues": []}
        all_issues_data = {"issues": []}
        resolved_issues_data = {"issues": []}


    issues = parse_jira_issues(jira_data)
    
    current_date_str = "2025-12-05"
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")

    total_descendants = all_issues_data.get("total", 0)
    oldest_resolution_date = get_oldest_resolution_date(resolved_issues_data)

    velocity = calculate_issue_completion_velocity(total_descendants, oldest_resolution_date, current_date)
    print(f"Issue Completion Velocity: {velocity}")


    for issue in issues.values():
        issue.calculate_weeks_active(current_date)
        issue.calculate_status_contribution()
        issue.calculate_computed_status_summary()
        issue.calculate_text_sentiment()
        if issue.key == "HCMSTRAT-17": # Only for the root issue
            issue.calculate_computed_delivery_date(current_date, total_descendants, velocity)
        issue.calculate_computed_color_status()

    # Find the root issue (assuming it's HCMSTRAT-17 for now)
    root_issue = issues.get("HCMSTRAT-17")
    if root_issue:
        perform_roll_ups(root_issue)
        report = generate_markdown_report(root_issue, velocity, open_descendants, total_descendants)
        print(report)

if __name__ == "__main__":
    main()
