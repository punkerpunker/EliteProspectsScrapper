import uuid


class Object:
    fields = []

    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        for field in kwargs:
            if field in self.fields:
                setattr(self, field, kwargs[field])

    def __repr__(self):
        return str(vars(self))


class Player(Object):
    file = 'Player.csv'
    fields = ['name', 'date_of_birth', 'position', 'age', 'height', 'place_of_birth', 'weight',
              'nation', 'shoots', 'youth_team', 'contract', 'cap_hit', 'nhl_rights', 'drafted']


class PlayerRegularSeasonStats(Object):
    file = 'PlayerRegularSeasonStats.csv'
    fields = ['year', 'team', 'league', 'games', 'goals', 'assists', 'points', 'penalty', 'plus_minus']

    def __init__(self, player_id, **kwargs):
        self.player_id = player_id
        super().__init__(**kwargs)
