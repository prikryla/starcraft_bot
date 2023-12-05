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

            # Trénování SCV v každém Command Centeru, dokud máte méně než 16 pracovníků na každé základně
            if self.can_afford(UnitTypeId.SCV):
                for command_center in self.townhalls.idle:
                    if command_center.assigned_harvesters < 16:
                        # Trénuj SCV z konkrétního Command Centeru
                        command_center.train(UnitTypeId.SCV)
                        print(f"Training SCV in Command Center {command_center.tag}")

            # Přiřadit pracovníky ke základnám
            await self.distribute_workers()

            # Stavba dalšího Command Centeru
            # Bot postaví další Command Center, pokud má dostatek prostředků
            if self.townhalls.amount < 2 and self.can_afford(UnitTypeId.COMMANDCENTER):
                # Další Command Center bude postaveno poblíž existujících budov
                await self.expand_now(UnitTypeId.COMMANDCENTER)


            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 9 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=command_center.position.towards(self.game_info.map_center, 8))
                                
            # Stavba Refinery
            # Bot staví tak dlouho, dokud si může dovolit stavět Refinery a jejich počet je menší než 2 pro každou základnu
            for command_center in self.townhalls:
                # Zkontrolovat, kolik rafinérií je postaveno u každé základny
                refineries_built = self.structures(UnitTypeId.REFINERY).closer_than(1, command_center)
                
                # Pokud je méně než 2 rafinérií, postav další
                if len(refineries_built) < 2:
                    # Najdi blízký vespene geyser, který ještě nemá postavenou rafinérii
                    vespene_geysers = self.vespene_geyser.closer_than(10, command_center)
                    for vespene in vespene_geysers:
                        if not self.structures(UnitTypeId.REFINERY).closer_than(1, vespene):
                            if self.can_afford(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY):
                                # Budova bude postavena poblíž vespene geyseru
                                await self.build(
                                    UnitTypeId.REFINERY,
                                    vespene)

            # Distribute workers evenly among refineries
            refineries = self.structures(UnitTypeId.REFINERY).ready
            workers = self.workers.idle

            # Ensure that each refinery has exactly 3 workers
            desired_workers_per_refinery = 3

            for refinery in refineries:
                # Check if the refinery already has the desired number of workers
                if refinery.assigned_harvesters < desired_workers_per_refinery:
                    # Assign workers to the refinery up to the desired count
                    workers_to_assign = min(desired_workers_per_refinery - refinery.assigned_harvesters, len(workers))
                    for _ in range(workers_to_assign):
                        worker = workers.pop(0)  # Take the first worker from the list
                        worker.gather(refinery)



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