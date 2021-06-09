from codes.scraping.j_league_data_site.j_match_schedule import j_match_schedule
from codes.scraping.j_league_data_site.j_rank_table import j_rank_table
from codes.scraping.j_league_data_site.j_starting_member import j_starting_member
from codes.scraping.toto.toto import toto

class  scraping_all():
    
    def __init__(self):
        self.j_match_schedule = j_match_schedule()
        self.j_rank_table = j_rank_table()
        self.j_starting_member = j_starting_member()
        self.toto = toto()
        
    def scraping_and_clean(self):
        
        # j_league_data_site
        self.j_match_schedule.scraping()
        self.j_match_schedule.clean()
        
        self.j_rank_table.scraping()
        self.j_rank_table.clean()
        
        self.j_starting_member.scraping()
        self.j_starting_member.clean()
        # toto
        self.toto.scraping()
        self.toto.clean()