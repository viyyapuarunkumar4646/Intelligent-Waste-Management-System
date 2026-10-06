"""
Intelligent Waste Management System - Version 2
Using IoT Sensors for Bin Fill Level Monitoring and Automated Collection Alerts
Enhanced with realistic waste accumulation and collection logic
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 10

class UltrasonicSensor:
    """Simulates ultrasonic sensor for measuring waste bin fill level"""
    
    def __init__(self, bin_id, bin_capacity_liters=240, sensor_accuracy=0.95):
        self.bin_id = bin_id
        self.bin_capacity_liters = bin_capacity_liters
        self.sensor_accuracy = sensor_accuracy
        self.current_fill_level = 0  # in percentage
        self.measurement_history = []
        self.last_measurement_time = None
        
    def measure_fill_level(self, actual_fill_level, current_time):
        """
        Measure waste bin fill level with sensor noise
        actual_fill_level: actual waste fill percentage (0-100%)
        Returns: measured fill level percentage (0-100)
        """
        # Add sensor noise (±3% accuracy variation)
        noise = np.random.normal(0, 3)
        measured_level = actual_fill_level + noise
        measured_level = np.clip(measured_level, 0, 100)
        
        self.current_fill_level = measured_level
        self.last_measurement_time = current_time
        
        self.measurement_history.append({
            'timestamp': current_time,
            'measured_level': measured_level,
            'actual_level': actual_fill_level,
            'sensor_accuracy': self.sensor_accuracy
        })
        
        return measured_level


class WasteCollectionAlert:
    """Manages collection alerts based on bin fill levels"""
    
    def __init__(self, alert_threshold=80, critical_threshold=95):
        self.alert_threshold = alert_threshold  # percentage
        self.critical_threshold = critical_threshold  # percentage
        self.alerts = []
        self.alert_history = []
        
    def check_alert_status(self, bin_id, fill_level, current_time):
        """
        Check if alert should be triggered based on fill level
        Returns: alert_type ('normal', 'warning', 'critical', 'urgent')
        """
        if fill_level >= self.critical_threshold:
            alert_type = 'urgent'
            priority = 'HIGH'
        elif fill_level >= self.alert_threshold:
            alert_type = 'critical'
            priority = 'MEDIUM'
        elif fill_level >= 60:
            alert_type = 'warning'
            priority = 'LOW'
        else:
            alert_type = 'normal'
            priority = 'NONE'
        
        if alert_type in ['critical', 'urgent']:
            alert = {
                'timestamp': current_time,
                'bin_id': bin_id,
                'fill_level': fill_level,
                'alert_type': alert_type,
                'priority': priority,
                'message': f"Bin {bin_id} fill level: {fill_level:.1f}%"
            }
            self.alerts.append(alert)
            self.alert_history.append(alert)
        
        return alert_type, priority


class WasteBin:
    """Represents a single waste bin with sensor and alert system"""
    
    def __init__(self, bin_id, bin_type='general', location='', capacity_liters=240):
        self.bin_id = bin_id
        self.bin_type = bin_type  # general, recyclable, organic, hazardous
        self.location = location
        self.capacity_liters = capacity_liters
        self.current_fill_level = 0  # in percentage (0-100)
        self.sensor = UltrasonicSensor(bin_id, capacity_liters)
        self.alert_manager = WasteCollectionAlert()
        self.fill_history = []
        self.collection_history = []
        self.last_collection_time = None
        self.total_collections = 0
        self.total_waste_collected = 0
        
    def add_waste(self, amount_percentage):
        """Add waste to the bin (in percentage of capacity)"""
        self.current_fill_level = min(100, self.current_fill_level + amount_percentage)
        
    def empty_bin(self, current_time):
        """Empty the bin during collection"""
        waste_collected = (self.current_fill_level / 100) * self.capacity_liters
        self.total_waste_collected += waste_collected
        self.current_fill_level = 0
        self.last_collection_time = current_time
        self.total_collections += 1
        
        self.collection_history.append({
            'timestamp': current_time,
            'collection_number': self.total_collections,
            'waste_collected_liters': waste_collected
        })
        
        return waste_collected


class WasteManagementSystem:
    """Main system managing multiple waste bins and collection operations"""
    
    def __init__(self):
        self.bins = {}
        self.collection_routes = []
        self.daily_statistics = []
        self.system_alerts = []
        self.collection_schedule = []
        
    def add_bin(self, bin_id, bin_type='general', location='', capacity_liters=240):
        """Add a waste bin to the system"""
        self.bins[bin_id] = WasteBin(bin_id, bin_type, location, capacity_liters)
        
    def simulate_day(self, date=None, num_intervals=48):
        """
        Simulate a full day with 30-minute intervals (48 intervals in 24 hours)
        """
        if date is None:
            date = datetime.now().date()
        
        daily_data = []
        total_waste_collected = 0
        total_collections = 0
        
        for interval in range(num_intervals):
            hour = (interval * 30) / 60  # Convert interval to hours
            time_of_day = int(hour)
            minutes = int((hour % 1) * 60)
            
            # Create timestamp
            current_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)
            
            for bin_id, bin_obj in self.bins.items():
                # Simulate waste generation patterns
                waste_generated_pct = self._generate_waste_pattern(bin_obj.bin_type, time_of_day)
                
                # Add waste to bin
                bin_obj.add_waste(waste_generated_pct)
                
                # Measure fill level with sensor
                measured_level = bin_obj.sensor.measure_fill_level(bin_obj.current_fill_level, current_time)
                
                # Check alert status
                alert_type, priority = bin_obj.alert_manager.check_alert_status(bin_id, measured_level, current_time)
                
                # Automatic collection if urgent
                waste_this_interval = 0
                if alert_type == 'urgent':
                    waste_this_interval = bin_obj.empty_bin(current_time)
                    total_waste_collected += waste_this_interval
                    total_collections += 1
                    measured_level = 0
                
                daily_data.append({
                    'date': date,
                    'time': f"{time_of_day:02d}:{minutes:02d}",
                    'hour': time_of_day,
                    'bin_id': bin_id,
                    'bin_type': bin_obj.bin_type,
                    'location': bin_obj.location,
                    'fill_level': measured_level,
                    'alert_type': alert_type,
                    'priority': priority,
                    'waste_generated_pct': waste_generated_pct,
                    'waste_collected_liters': waste_this_interval,
                    'total_collections': total_collections
                })
        
        avg_fill = np.mean([self.bins[b].current_fill_level for b in self.bins])
        
        self.daily_statistics.append({
            'date': date,
            'total_waste_collected_liters': total_waste_collected,
            'total_collections': total_collections,
            'num_bins': len(self.bins),
            'avg_fill_level': avg_fill
        })
        
        return pd.DataFrame(daily_data)
    
    def _generate_waste_pattern(self, bin_type, hour):
        """Generate realistic waste generation patterns (as percentage of capacity per 30 min)"""
        # General waste: peaks during lunch (12-14h) and evening (18-20h)
        if bin_type == 'general':
            if 12 <= hour < 14:
                base_waste = 3.5 + np.random.normal(0, 0.8)
            elif 18 <= hour < 20:
                base_waste = 3.0 + np.random.normal(0, 0.8)
            elif 8 <= hour < 12 or 14 <= hour < 18:
                base_waste = 1.2 + np.random.normal(0, 0.3)
            else:
                base_waste = 0.4 + np.random.normal(0, 0.2)
        
        # Recyclable waste: steady throughout day
        elif bin_type == 'recyclable':
            base_waste = 0.8 + np.random.normal(0, 0.2)
        
        # Organic waste: peaks during meal times
        elif bin_type == 'organic':
            if 12 <= hour < 14 or 18 <= hour < 20:
                base_waste = 2.2 + np.random.normal(0, 0.5)
            else:
                base_waste = 0.4 + np.random.normal(0, 0.1)
        
        # Hazardous waste: minimal and sporadic
        else:
            base_waste = 0.2 + np.random.normal(0, 0.1) if np.random.random() > 0.85 else 0.05
        
        return max(0, base_waste)
    
    def get_system_report(self):
        """Generate comprehensive system report"""
        report = {
            'total_bins': len(self.bins),
            'bin_types': list(set([self.bins[b].bin_type for b in self.bins])),
            'total_waste_collected_liters': sum([stat['total_waste_collected_liters'] for stat in self.daily_statistics]),
            'total_collections': sum([stat['total_collections'] for stat in self.daily_statistics]),
            'simulation_days': len(self.daily_statistics),
            'avg_daily_collections': np.mean([stat['total_collections'] for stat in self.daily_statistics]) if self.daily_statistics else 0,
            'avg_daily_waste_liters': np.mean([stat['total_waste_collected_liters'] for stat in self.daily_statistics]) if self.daily_statistics else 0
        }
        return report


def generate_visualizations(system, daily_data):
    """Generate comprehensive visualizations for the report"""
    
    # 1. Bin Fill Level Analysis
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Intelligent Waste Management System - Fill Level Analysis', fontsize=16, fontweight='bold')
    
    # Fill level by bin type
    fill_by_type = daily_data.groupby('bin_type')['fill_level'].mean()
    axes[0, 0].bar(fill_by_type.index, fill_by_type.values, color='steelblue', edgecolor='black')
    axes[0, 0].set_title('Average Fill Level by Bin Type', fontweight='bold')
    axes[0, 0].set_ylabel('Fill Level (%)')
    axes[0, 0].set_xlabel('Bin Type')
    axes[0, 0].tick_params(axis='x', rotation=45)
    axes[0, 0].axhline(y=80, color='red', linestyle='--', linewidth=2, label='Alert Threshold')
    axes[0, 0].legend()
    for i, v in enumerate(fill_by_type.values):
        axes[0, 0].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
    
    # Fill level pattern throughout the day
    fill_by_hour = daily_data.groupby('hour')['fill_level'].mean()
    axes[0, 1].plot(fill_by_hour.index, fill_by_hour.values, marker='o', 
                    linewidth=2, markersize=6, color='green')
    axes[0, 1].fill_between(fill_by_hour.index, fill_by_hour.values, alpha=0.3, color='green')
    axes[0, 1].axhline(y=80, color='red', linestyle='--', linewidth=2, label='Alert Threshold')
    axes[0, 1].set_title('Fill Level Pattern Throughout the Day', fontweight='bold')
    axes[0, 1].set_ylabel('Fill Level (%)')
    axes[0, 1].set_xlabel('Hour of Day')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend()
    axes[0, 1].set_ylim([0, 100])
    
    # Alert distribution
    alert_counts = daily_data['alert_type'].value_counts()
    colors_map = {'normal': 'green', 'warning': 'yellow', 'critical': 'orange', 'urgent': 'red'}
    colors = [colors_map.get(alert, 'gray') for alert in alert_counts.index]
    axes[1, 0].bar(alert_counts.index, alert_counts.values, color=colors, edgecolor='black')
    axes[1, 0].set_title('Alert Distribution', fontweight='bold')
    axes[1, 0].set_ylabel('Count')
    axes[1, 0].set_xlabel('Alert Type')
    for i, v in enumerate(alert_counts.values):
        axes[1, 0].text(i, v + 2, str(v), ha='center', fontweight='bold')
    
    # Collection efficiency
    collections_by_hour = daily_data.groupby('hour')['total_collections'].max().diff().fillna(0)
    axes[1, 1].bar(collections_by_hour.index, collections_by_hour.values, color='purple', edgecolor='black', alpha=0.7)
    axes[1, 1].set_title('Collections per Hour', fontweight='bold')
    axes[1, 1].set_ylabel('Number of Collections')
    axes[1, 1].set_xlabel('Hour of Day')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/waste_report_project/fig_fill_level_analysis.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_fill_level_analysis.png")
    plt.close()
    
    # 2. Alert Priority Distribution
    fig, ax = plt.subplots(figsize=(12, 6))
    
    priority_counts = daily_data['priority'].value_counts()
    priority_order = ['NONE', 'LOW', 'MEDIUM', 'HIGH']
    priority_counts = priority_counts.reindex([p for p in priority_order if p in priority_counts.index], fill_value=0)
    
    colors_priority = {'NONE': 'green', 'LOW': 'yellow', 'MEDIUM': 'orange', 'HIGH': 'red'}
    colors = [colors_priority.get(p, 'gray') for p in priority_counts.index]
    
    ax.bar(priority_counts.index, priority_counts.values, color=colors, edgecolor='black', width=0.6)
    ax.set_xlabel('Alert Priority', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('Alert Priority Distribution', fontweight='bold', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    
    for i, v in enumerate(priority_counts.values):
        ax.text(i, v + 5, str(int(v)), ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/waste_report_project/fig_alert_priority.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_alert_priority.png")
    plt.close()
    
    # 3. Bin Performance Comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bin_performance = daily_data.groupby('bin_id').agg({
        'fill_level': 'mean',
        'alert_type': lambda x: (x.isin(['critical', 'urgent'])).sum()
    }).rename(columns={'alert_type': 'alerts_triggered'})
    
    x = np.arange(len(bin_performance))
    width = 0.35
    
    ax.bar(x - width/2, bin_performance['fill_level'], width, label='Avg Fill Level (%)', 
           color='steelblue', edgecolor='black')
    ax2 = ax.twinx()
    ax2.bar(x + width/2, bin_performance['alerts_triggered'], width, label='Alerts Triggered', 
            color='red', alpha=0.7, edgecolor='black')
    
    ax.set_xlabel('Bin ID', fontweight='bold')
    ax.set_ylabel('Average Fill Level (%)', fontweight='bold', color='steelblue')
    ax2.set_ylabel('Number of Alerts', fontweight='bold', color='red')
    ax.set_title('Bin Performance Comparison', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(bin_performance.index)
    ax.grid(True, alpha=0.3, axis='y')
    
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/waste_report_project/fig_bin_performance.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_bin_performance.png")
    plt.close()
    
    # 4. Waste Collection Efficiency
    fig, ax = plt.subplots(figsize=(12, 6))
    
    waste_by_hour = daily_data.groupby('hour')['waste_collected_liters'].sum()
    
    ax.bar(waste_by_hour.index, waste_by_hour.values, color='orange', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Hour of Day', fontweight='bold')
    ax.set_ylabel('Waste Collected (liters)', fontweight='bold')
    ax.set_title('Waste Collection Efficiency by Hour', fontweight='bold', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/waste_report_project/fig_waste_collection.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_waste_collection.png")
    plt.close()
    
    # 5. System Architecture Diagram
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'Intelligent Waste Management System Architecture', 
            ha='center', fontsize=16, fontweight='bold', transform=ax.transAxes)
    
    components = [
        ('Ultrasonic\nSensors', 0.15, 0.75),
        ('IoT\nCommunication', 0.5, 0.75),
        ('Cloud\nServer', 0.85, 0.75),
        ('Alert\nSystem', 0.5, 0.50),
        ('Collection\nManagement', 0.15, 0.50),
        ('Analytics\nDashboard', 0.85, 0.50),
    ]
    
    for label, x, y in components:
        bbox = dict(boxstyle='round,pad=0.6', facecolor='lightblue', edgecolor='black', linewidth=2)
        ax.text(x, y, label, ha='center', va='center', fontsize=11, fontweight='bold',
                transform=ax.transAxes, bbox=bbox)
    
    connections = [
        ((0.25, 0.75), (0.4, 0.75)),
        ((0.6, 0.75), (0.75, 0.75)),
        ((0.5, 0.65), (0.5, 0.60)),
        ((0.25, 0.65), (0.25, 0.60)),
        ((0.75, 0.65), (0.75, 0.60)),
    ]
    
    for start, end in connections:
        ax.annotate('', xy=end, xytext=start, transform=ax.transAxes,
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    features_text = 'Key Features:\n• Real-time Fill Level Monitoring\n• Automated Collection Alerts\n• Route Optimization\n• Cost Reduction\n• Environmental Sustainability'
    ax.text(0.5, 0.20, features_text, ha='center', va='top', fontsize=10,
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightyellow', 
            edgecolor='black', linewidth=1.5))
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/waste_report_project/fig_system_architecture.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_system_architecture.png")
    plt.close()


def main():
    """Main execution function"""
    print("=" * 70)
    print("INTELLIGENT WASTE MANAGEMENT SYSTEM SIMULATION")
    print("=" * 70)
    
    # Initialize system
    system = WasteManagementSystem()
    
    # Add bins with different types and locations
    bins_config = {
        'BIN-001': {'type': 'general', 'location': 'Main Entrance'},
        'BIN-002': {'type': 'recyclable', 'location': 'Office Area'},
        'BIN-003': {'type': 'organic', 'location': 'Cafeteria'},
        'BIN-004': {'type': 'general', 'location': 'Parking Area'},
        'BIN-005': {'type': 'hazardous', 'location': 'Laboratory'},
    }
    
    for bin_id, config in bins_config.items():
        system.add_bin(bin_id, config['type'], config['location'])
    
    print(f"\nSystem initialized with {len(bins_config)} bins:")
    for bin_id, config in bins_config.items():
        print(f"  - {bin_id}: {config['type']} ({config['location']})")
    
    # Simulate 7 days
    print("\nSimulating 7 days of operation...")
    all_data = []
    
    for day in range(7):
        simulation_date = datetime.now().date() - timedelta(days=6-day)
        daily_data = system.simulate_day(simulation_date)
        all_data.append(daily_data)
        
        daily_stats = system.daily_statistics[-1]
        print(f"Day {day+1} ({simulation_date}): Collections={daily_stats['total_collections']}, "
              f"Waste={daily_stats['total_waste_collected_liters']:.1f}L, "
              f"Avg Fill={daily_stats['avg_fill_level']:.1f}%")
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    generate_visualizations(system, combined_data)
    
    # Generate report data
    report = system.get_system_report()
    
    print("\n" + "=" * 70)
    print("SYSTEM REPORT")
    print("=" * 70)
    print(f"Total Bins: {report['total_bins']}")
    print(f"Bin Types: {', '.join(report['bin_types'])}")
    print(f"Total Waste Collected: {report['total_waste_collected_liters']:.1f} liters")
    print(f"Total Collections: {report['total_collections']}")
    print(f"Average Daily Collections: {report['avg_daily_collections']:.1f}")
    print(f"Average Daily Waste: {report['avg_daily_waste_liters']:.1f} liters")
    print(f"Simulation Period: {report['simulation_days']} days")
    print("=" * 70)
    
    # Save data to CSV
    combined_data.to_csv('/home/ubuntu/waste_report_project/simulation_data.csv', index=False)
    print("\nSimulation data saved to: simulation_data.csv")
    
    # Save report to JSON
    report_json = {
        'system_report': report,
        'bins': list(bins_config.keys()),
        'simulation_date': datetime.now().isoformat(),
        'daily_statistics': system.daily_statistics
    }
    
    with open('/home/ubuntu/waste_report_project/system_report.json', 'w') as f:
        json.dump(report_json, f, indent=2, default=str)
    
    print("System report saved to: system_report.json")
    
    return system, combined_data


if __name__ == "__main__":
    system, data = main()
