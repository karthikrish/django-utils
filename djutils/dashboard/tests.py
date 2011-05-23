import datetime

from djutils.dashboard.models import Panel, PanelData, PanelDataSet
from djutils.dashboard.provider import PanelProvider
from djutils.dashboard.registry import registry
from djutils.test import TestCase


class TestPanelA(PanelProvider):
    _i = 0
    
    def get_title(self):
        return 'a'
    
    def get_data(self):
        TestPanelA._i += 1
        return {
            'a': TestPanelA._i,
            'x': 1,
        }


class TestPanelB(PanelProvider):
    def get_title(self):
        return 'b'
    
    def get_data(self):
        return {'b': 1}


class BasePanelTestCase(TestCase):
    def setUp(self):
        TestPanelA._i = 0
        
        registry.register(TestPanelA)
        registry.register(TestPanelB)
        
        self.panel_a = Panel.objects.create(title='a', slug='a')
        self.panel_b = Panel.objects.create(title='b', slug='b')
        
        self.seed = datetime.datetime(2011, 1, 1)
    
    def tearDown(self):
        registry.unregister(TestPanelA)
        registry.unregister(TestPanelB)
    
    def create_data(self, seed, how_much=60):
        cur_time = seed
        
        for i in range(1, how_much + 1):
            
            for provider in registry.get_provider_instances():
                # pull the data off the panel and store
                panel_obj = provider.get_panel_instance()
                
                panel_data_obj = PanelData.objects.create(
                    panel=panel_obj,
                    created_date=cur_time,
                )
                
                raw_panel_data = provider.get_data()
                
                for key, value in raw_panel_data.items():
                    data_set_obj = PanelDataSet.objects.create(
                        panel_data=panel_data_obj,
                        key=key,
                        value=value,
                    )
        
            if i % 60 == 0:
                Panel.objects.generate_hourly_aggregates(cur_time)
        
            if i % 1440 == 0:
                Panel.objects.generate_daily_aggregates(cur_time)
            
            cur_time += datetime.timedelta(seconds=60)
    
    def clear_data(self):
        Panel.objects.all().delete()


class PanelModelTestCase(BasePanelTestCase):
    def test_panel_registry_to_model(self):
        self.assertEqual(len(registry._registry), 2)
        self.assertEqual(Panel.objects.count(), 2)
        
        provider_a = registry._registry[TestPanelA]
        provider_b = registry._registry[TestPanelB]
        
        # behind-the-scenes does a get-or-create
        panel_model_a = provider_a.get_panel_instance()
        self.assertEqual(panel_model_a, self.panel_a)
        
        panel_model_b = provider_b.get_panel_instance()
        self.assertEqual(panel_model_b, self.panel_b)
        
        # ensure that no new instances were created
        self.assertEqual(Panel.objects.count(), 2)
        
        # blow away all the panels
        Panel.objects.all().delete()
        
        panel_model_a = provider_a.get_panel_instance()
        panel_model_b = provider_b.get_panel_instance()
        
        self.assertEqual(Panel.objects.count(), 2)
    
    def test_basic_data_generation(self):
        self.create_data(self.seed)
        
        for panel in (self.panel_a, self.panel_b):
            # check to see that 60 minutes of data was generated
            self.assertEqual(panel.data.minute_data().count(), 60)
            
            # check to see that 1 hour of aggregate data was generated
            self.assertEqual(panel.data.hour_data().count(), 1)
            
            # no data for the day should have been generated
            self.assertEqual(panel.data.day_data().count(), 0)
        
        minute_list = list(self.panel_a.data.minute_data())
        first, last = minute_list[-1], minute_list[0]
        
        self.assertEqual(first.created_date, datetime.datetime(2011, 1, 1, 0, 0))
        self.assertEqual(last.created_date, datetime.datetime(2011, 1, 1, 0, 59))
        
        hour = list(self.panel_a.data.hour_data())[0]
        
        self.assertEqual(hour.created_date, datetime.datetime(2011, 1, 1, 0, 59))
        
        self.assertEqual(first.get_data(), {
            'a': 1.0,
            'x': 1.0,
        })
        
        self.assertEqual(last.get_data(), {
            'a': 60.0,
            'x': 1.0,
        })
        
        self.assertEqual(hour.get_data(), {
            'a': 30.5,
            'x': 1.0,
        })
