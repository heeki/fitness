import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

class StravaAnalyzer:
    # Conversion factors
    METERS_TO_MILES = 0.000621371
    MPS_TO_MPH = 2.23694
    METERS_TO_FEET = 3.28084

    def __init__(self):
        self.fields_to_remove = ['athlete', 'map', 'start_latlng', 'end_latlng']

    def clean_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Remove unnecessary fields from activity data and convert units"""
        cleaned = {k: v for k, v in activity.items() if k not in self.fields_to_remove}

        # Convert metric units to imperial
        if 'distance' in cleaned:
            cleaned['distance'] = cleaned['distance'] * self.METERS_TO_MILES
        if 'elev_high' in cleaned:
            cleaned['elev_high'] = cleaned['elev_high'] * self.METERS_TO_FEET
        if 'elev_low' in cleaned:
            cleaned['elev_low'] = cleaned['elev_low'] * self.METERS_TO_FEET
        if 'average_speed' in cleaned:
            cleaned['average_speed'] = cleaned['average_speed'] * self.MPS_TO_MPH
        if 'max_speed' in cleaned:
            cleaned['max_speed'] = cleaned['max_speed'] * self.MPS_TO_MPH
        if 'total_elevation_gain' in cleaned:
            cleaned['total_elevation_gain'] = cleaned['total_elevation_gain'] * self.METERS_TO_FEET

        return cleaned

    def clean_activities(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean a list of activities"""
        return [self.clean_activity(activity) for activity in activities]

    def convert_to_csv(self, activities: List[Dict[str, Any]], output_file: str) -> None:
        """Convert activities data to CSV format and save to file"""
        try:
            # Clean the activities data
            cleaned_activities = self.clean_activities(activities)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Write to CSV
            with open(output_file, 'w', newline='') as f:
                if cleaned_activities:
                    writer = csv.DictWriter(f, fieldnames=cleaned_activities[0].keys())
                    writer.writeheader()
                    writer.writerows(cleaned_activities)
                    print(f"Successfully converted {len(cleaned_activities)} activities to CSV")
                else:
                    print("No activities found in the input data")

        except Exception as e:
            print(f"Error writing CSV: {str(e)}")

    def _calculate_activity_stats(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Helper method to calculate statistics for a list of activities"""
        if not activities:
            return {}

        # Calculate basic statistics
        total_distance = sum(activity.get('distance', 0) for activity in activities)
        total_moving_time = sum(activity.get('moving_time', 0) for activity in activities)
        total_elapsed_time = sum(activity.get('elapsed_time', 0) for activity in activities)

        # Count activities by type
        activity_types = {}
        for activity in activities:
            activity_type = activity.get('type', 'Unknown')
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1

        return {
            'total_activities': len(activities),
            'total_distance_miles': total_distance,  # Already converted to miles in clean_activity
            'total_moving_time_hours': total_moving_time / 3600,  # Convert seconds to hours
            'total_elapsed_time_hours': total_elapsed_time / 3600,  # Convert seconds to hours
            'activity_types': activity_types
        }

    def get_activities_summary(self, activities: List[Dict[str, Any]], include_weekly: bool = True) -> Dict[str, Any]:
        """Generate a summary of activities data, optionally including weekly breakdowns

        Args:
            activities: List of activity dictionaries
            include_weekly: Whether to include weekly summaries (default: True)

        Returns:
            Dictionary containing overall summary and optionally weekly summaries
        """
        if not activities:
            return {}

        cleaned_activities = self.clean_activities(activities)

        # Calculate overall summary
        overall_summary = self._calculate_activity_stats(cleaned_activities)

        result = {
            'overall': overall_summary
        }

        if include_weekly:
            # Group activities by week
            weekly_activities = defaultdict(list)
            for activity in cleaned_activities:
                # Parse the start date and get the week start (Monday)
                start_date = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
                # Get the Monday of the week
                week_start = start_date - timedelta(days=start_date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                weekly_activities[week_key].append(activity)

            # Calculate summary for each week
            weekly_summaries = {}
            for week_start, week_activities in sorted(weekly_activities.items()):
                weekly_summaries[week_start] = self._calculate_activity_stats(week_activities)

            result['weekly'] = weekly_summaries

        return result