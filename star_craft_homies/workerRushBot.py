from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId

class WorkerRushBot(BotAI):
    NAME: str = "WorkerRushBot"
    RACE: Race = Race.Terran

    async def on_step(self, iteration: int):
        # Jestliže mám Command Center
        if self.townhalls:
            # První Command Center
            command_center = self.townhalls[0]

            # Trénování SCV
            # Bot trénuje nová SCV, jestliže je jich méně než 17
            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= 16 and command_center.is_idle:
                command_center.train(UnitTypeId.SCV)

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 9 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=command_center.position.towards(self.game_info.map_center, 8))
                    
            # # Stavba Refinery
            # # Bot staví tak dlouho, dokud si může dovolit stavět Refinery a jejich počet je menší než 2
            if self.already_pending(UnitTypeId.REFINERY) == 0:
                # Je jich méně než 2 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.REFINERY).amount < 2:
                    # Najdi blízký vespene geyser, který ještě nemá postavenou rafinérii
                    vespene_geyser = self.vespene_geyser.closer_than(10, command_center)
                    for vespene in vespene_geyser:
                        if not self.structures(UnitTypeId.REFINERY).closer_than(1, vespene):
                            if self.can_afford(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY):
                                # Budova bude postavena poblíž vespene geyseru
                                await self.build(
                                    UnitTypeId.REFINERY,
                                    vespene)
                                                
                for scv in self.workers.idle:
                    for refinery in self.structures(UnitTypeId.REFINERY).ready:
                        # Ensure that the worker is not already assigned to the refinery
                        if scv.order_target != refinery.tag:
                            scv.gather(refinery)

            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=command_center.position.towards(self.game_info.map_center, 8))

            # Trénování jednotky Marine
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.MARINE):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                    barrack.train(UnitTypeId.MARINE)

            # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
            idle_marines = self.units(UnitTypeId.MARINE).idle
            if idle_marines.amount > 15:
                target = self.enemy_structures.random_or(
                    self.enemy_start_locations[0]).position
                for marine in idle_marines:
                    marine.attack(target)


run_game(maps.get("sc2-ai-cup-2022"), [
    Bot(Race.Terran, WorkerRushBot()),
    Computer(Race.Terran, Difficulty.Medium)
], realtime=False)