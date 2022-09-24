from typing import Iterable
from random import randint
from pathlib import Path
from os import path
import pygame as pg

from lib.object import Star
from lib.object import Text, Color, Button, Colors, ButtonEvent, TextShadowEffect
from lib.object import Player, Enemy

BASEDIR = Path(__file__).parent.parent.absolute()

def font_located(fontname):
    # return f'assets/font/{fontname}.ttf'
    return path.join(BASEDIR, 'assets', 'font', fontname+'.ttf')

class Scene:
    def __init__(self):
        self.groups = {}
        self.raws = {}
        
    def add_item(self, name, *sprites:Iterable[pg.sprite.Sprite]):
        self.groups[name].add(sprites)
    
    def add_raw_item(self, item, center, name):
        self.raws[name] = [item, list(center)]
    
    def create_group(self, name, *sprites:Iterable[pg.sprite.Sprite]):
        self.groups[name] = pg.sprite.Group(sprites)
        return self.groups[name]

    def remove_group(self, name):
        del self.groups[name]
    
    def update(self, events):
        for groups in self.groups.values():
            groups.update(events)
    
    def render(self, screen):
        for groups in self.groups.values():
            for item in groups:
                item.render(screen)
        
        for item,center in self.raws.values():
            screen.blit(item, item.get_rect(center=center))
    
    def inherit_groups(self, *group_names):
        return {name: self.groups[name] for name in group_names}

star_effect_delay = 250

class MenuScene(Scene):
    def __init__(self, gameObject, data):
        super().__init__()
        self.screen_color = Colors.BLACK.as_iter()
        
        title_font = pg.font.Font(font_located('BlackHanSans-Regular'), 40)
        button_font = pg.font.Font(font_located('ONE Mobile Bold'), 30)
        title = Text("부평고 2022 코딩동아리 게임", 
                     title_font, 
                     Colors.ORANGE,
                     (
                         gameObject.screen.get_width() / 2, 
                         gameObject.screen.get_height() / 6
                     ),
                     TextShadowEffect(Colors.ORANGE + Color(20, 20, 20), (2, 2)))
        self.create_group("title", title)
        
        BUTTON_COLOR = [
            Colors.ORANGE,
            Colors.RED,
            Colors.RED - Color(100, 0, 0)
        ]
        
        start_button = Button(
            (200, 50),
            (
                gameObject.screen.get_width() / 2,
                gameObject.screen.get_height() / 8 * 5 - 40
            ),
            BUTTON_COLOR,
            Text("시작하기", button_font, Colors.WHITE),
            ButtonEvent(gameObject, lambda gameObject: gameObject.change_scene(MenuGameTransition, {
                "inheritGroups": self.inherit_groups("title", "buttons", "stars"), 
                "lastStarCreation": self.last_star_creation
                }))
        ),
        help_button = Button(
            (200, 50),
            (
                gameObject.screen.get_width() / 2,
                gameObject.screen.get_height() / 8 * 5 + 40
            ),
            BUTTON_COLOR,
            Text("도움말", button_font, Colors.WHITE),
            ButtonEvent(gameObject, lambda gameObject: gameObject.change_scene(HowToPlayScene))
        )
        quit_button = Button(
            (200, 50),
            (
                gameObject.screen.get_width() / 2,
                gameObject.screen.get_height() / 8 * 5 + 120
            ),
            BUTTON_COLOR,
            Text("종료하기", button_font, Colors.WHITE),
            ButtonEvent(gameObject, lambda gameObject: gameObject.quit())
        )
        self.create_group("buttons", start_button, help_button, quit_button)
        
        # for star effect
        if "inheritGroups" in data and "stars" in data["inheritGroups"]:
            self.groups["stars"] = data["inheritGroups"]["stars"]
        else:
            self.create_group("stars")
        if "lastStarCreation" in data:
            self.last_star_creation = data["lastStarCreation"]
        else:
            self.last_star_creation = pg.time.get_ticks()
    
    def update(self, events):
        super().update(events)
        # star effect
        if pg.time.get_ticks() - self.last_star_creation > star_effect_delay:
            self.add_item("stars", Star(randint(0, pg.display.get_window_size()[0]), randint(0, pg.display.get_window_size()[1])))
            self.last_star_creation = pg.time.get_ticks()

class MenuGameTransition(Scene):
    def __init__(self, gameObject, data):
        self.screen_color = Colors.BLACK.as_iter()
        super().__init__()
        self.groups: dict = data["inheritGroups"]
        self.scene_start_time = pg.time.get_ticks()
        
        self.power_factor_a = 1.0042
        self.start_time = 100
        
        self.push_power = lambda currentTime: self.power_factor_a ** (currentTime + self.start_time)
        
        self.gameObject = gameObject
        self.transitionFinishedTime = None
        self.transitionFinishDelay = 500

        # for star effect
        self.last_star_creation = data["lastStarCreation"]
    
    def update(self, events):
        # star effect
        if pg.time.get_ticks() - self.last_star_creation > star_effect_delay:
            self.add_item("stars", Star(randint(0, pg.display.get_window_size()[0]), randint(0, pg.display.get_window_size()[1])))
            self.last_star_creation = pg.time.get_ticks()
        # main update
        for name, group in self.groups.copy().items():
            if not group:
                del self.groups[name]
        if "title" not in (keys:=self.groups.keys()) and "buttons" not in keys:
            if self.transitionFinishedTime == None:
                self.transitionFinishedTime = pg.time.get_ticks()
            elif pg.time.get_ticks() - self.transitionFinishedTime > self.transitionFinishDelay:
                self.gameObject.change_scene(GameScene, {"inheritGroups": self.inherit_groups("stars"), "lastStarCreation": self.last_star_creation})
        elapsed_time = pg.time.get_ticks() - self.scene_start_time
        if "title" in self.groups.keys():
            for item in self.groups["title"]:
                item.rect.y -= self.push_power(elapsed_time)
                if item.rect.bottom < 0:
                    self.groups["title"].remove(item)
        if "buttons" in self.groups.keys():
            for item in self.groups["buttons"]:
                item.disabled = True
                item.rect.y += self.push_power(elapsed_time)
                if item.rect.top > self.gameObject.screen.get_height():
                    self.groups["buttons"].remove(item)
        
        super().update(events)

class GameScene(Scene):
    def __init__(self, gameObject, data):
        self.game = gameObject
        super().__init__()
        self.started_time = pg.time.get_ticks()
        self.screen_color = Colors.BLACK.as_iter()
        
        self.player = Player((gameObject.screen.get_width() // 2, gameObject.screen.get_height() // 2), Colors.BLUE)
        self.create_group("player", self.player)
        
        self.score_display_font = pg.font.Font(font_located('INVASION2000'), 60)
        self.score_displayer = self.score_display_font.render("0", True, Colors.ORANGE.as_iter())
        self.add_raw_item(self.score_displayer, (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 8),"score_displayer")
        
        self.score = 0
        self.summon_count = 0
        self.last_summon_time = 0
        self.lower_limit = 100
        
        self.target_x_range = 50  # * 2
        self.target_y_range = 50  # * 2
        
        self.create_group("enemy")
        
        # for star effect
        self.groups["stars"] = data["inheritGroups"]["stars"]
        self.last_star_creation = data["lastStarCreation"]
    
    def update(self, events):
        # star effect
        if pg.time.get_ticks() - self.last_star_creation > star_effect_delay:
            self.add_item("stars", Star(randint(0, pg.display.get_window_size()[0]), randint(0, pg.display.get_window_size()[1])))
            self.last_star_creation = pg.time.get_ticks()
        # main update
        elapsed_time = pg.time.get_ticks() - self.started_time
        
        def hit_test(item, offset):
            return self.player.mask.overlap(item.mask, offset)
        
        def normal_hit(item):
            self.player.set_test_hitbox("normal_hitbox")
            return hit_test(item, (self.player.rect.x - item.rect.x,
                             self.player.rect.y - item.rect.y))
        
        def point_hit(item):
            self.player.set_test_hitbox("point_hitbox")
            return hit_test(item, (((self.player.rect.x - (self.player.point_hitbox_expand_x / 2)) -item.rect.x),
                                   ((self.player.rect.y - (self.player.point_hitbox_expand_y / 2)) - item.rect.y)))
        
        for item in self.groups["enemy"].sprites():
            self.player.set_test_hitbox("normal_hitbox")
            if normal_hit(item):
                self.player.kill()
                self.game.change_scene(ResultScene, {"inheritGroups": self.inherit_groups("enemy", "stars"), "elapsedTime": elapsed_time, "score": self.score, "totalScore": elapsed_time + self.score, "lastStarCreation": self.last_star_creation})
            elif point_hit(item) and not item.counted:
                item.counted = True
                self.score += 2000
        
        enemy_summon_delay_pattern = lambda x: -0.000005 * (x ** 2) + 500
        summon_delay = enemy_summon_delay_pattern(elapsed_time)
        if summon_delay <= self.lower_limit:
            summon_delay = self.lower_limit
        print(f"elapsed: {elapsed_time}, summon: {self.last_summon_time+summon_delay}, delay: {summon_delay}", end="\r")
        
        if elapsed_time > self.last_summon_time + summon_delay:
            self.add_item("enemy", Enemy(
                randint(-5, 5),
                randint(-5, 5),
                (
                    randint(self.player.rect.x - self.target_x_range, self.player.rect.x + self.target_x_range),
                    randint(self.player.rect.y - self.target_y_range, self.player.rect.y + self.target_y_range)
                ),
                True if randint(0, 1) == 1 else False,
                True if randint(0, 1) == 1 else False,
                self.game.screen.get_size(),
                Colors.RED
            ))
            self.last_summon_time = elapsed_time
        
        self.raws["score_displayer"][0] = self.score_display_font.render(str(elapsed_time), True, Colors.ORANGE.as_iter())
        
        super().update(events)

class ResultScene(Scene):
    def __init__(self, gameObject, data):
        super().__init__()
        self.scene_start_time = pg.time.get_ticks()
        self.last_update_time = self.scene_start_time
        self.screen_color = Colors.BLACK.as_iter()
        self.groups = data["inheritGroups"]
        self.screen = gameObject.screen
        
        self.score = data["score"]
        self.elapsed_time = data["elapsedTime"]
        self.total_score = data["totalScore"]
        
        self.anim_current_score = 0
        self.anim_current_elapsed_time = 0
        self.anim_current_total_score = 0
        
        button_font = pg.font.Font(font_located('One Mobile Bold'), 30)
        
        title = Text(
            "Game Over", 
            pg.font.Font(font_located('BlackHanSans-Regular'), 40), 
            Colors.ORANGE, 
            (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 5),
            TextShadowEffect(Colors.ORANGE + Color(20, 20, 20), (2, 2)))
        self.create_group("title", title)
        
        BUTTON_COLOR = [
            Colors.ORANGE,
            Colors.RED,
            Colors.RED - Color(100, 0, 0)
        ]
        
        self.score_displayer_font = pg.font.Font(font_located('INVASION2000'), 40)
        self.score_displayer = self.score_displayer_font.render("0", True, Colors.ORANGE.as_iter())
        
        self.score_comment_font = pg.font.Font(font_located('BlackHanSans-Regular'), 40)
        self.score_comment_overall = self.score_comment_font.render("총 점수", True, (Colors.RED - Color(50, 0, 0)).as_iter())
        self.score_comment_time = self.score_comment_font.render("시간 점수", True, (Colors.RED - Color(50, 0, 0)).as_iter())
        self.score_comment_barely_missed = self.score_comment_font.render("액션 점수", True, (Colors.RED - Color(50, 0, 0)).as_iter())
        
        self.score_splitted_time = self.score_displayer_font.render("0", True, Colors.ORANGE.as_iter())
        self.score_splitted_barely_missed = self.score_displayer_font.render("0", True, Colors.ORANGE.as_iter())
        
        self.add_raw_item(self.score_displayer, (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 5 + 100), "score_displayer")
        self.add_raw_item(self.score_comment_overall, (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 5 + 70), "score_comment_overall")
        self.add_raw_item(self.score_comment_time, (gameObject.screen.get_width() / 4, gameObject.screen.get_height() / 5 + 170), "score_comment_time")
        self.add_raw_item(self.score_comment_barely_missed, (gameObject.screen.get_width() / 4 * 3, gameObject.screen.get_height() / 5 + 170), "score_comment_barely_missed")
        self.add_raw_item(self.score_splitted_time, (gameObject.screen.get_width() / 4, gameObject.screen.get_height() / 5 + 200), "score_splitted_time")
        self.add_raw_item(self.score_splitted_barely_missed, (gameObject.screen.get_width() / 4 * 3, gameObject.screen.get_height() / 5 + 200), "score_splitted_barely_missed")
        
        self.score_animation_time_delay = 20
        self.score_animation_barely_missed_delay = 20
        self.score_animation_time_chunk = 100
        self.score_animation_barely_missed_chunk = 100
        
        self.animation_finished = False
        self.score_time_animation_finished = False
        self.score_time_animation_finished_time = None
        self.score_barely_missed_animation_finished = False
        self.score_barely_missed_animation_finished_time = None
        
        self.score_time_animation_finish_delay = 300
        
        self.RestartBtn = Button(
            (200, 50),
            (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 8 * 5 - 40),
            BUTTON_COLOR,
            Text("다시하기", button_font, Colors.WHITE),
            ButtonEvent(gameObject, lambda gameObject: gameObject.change_scene(GameScene, {"inheritGroups": self.inherit_groups("stars"), "lastStarCreation": self.last_star_creation})),
        )
        
        self.MenuBtn = Button(
            (200, 50),
            (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 8 * 5 + 40),
            BUTTON_COLOR,
            Text("메뉴로", button_font, Colors.WHITE),
            ButtonEvent(gameObject, lambda gameObject: gameObject.change_scene(MenuScene, {"inheritGroups": self.inherit_groups("stars"), "lastStarCreation": self.last_star_creation}))
        )
        
        self.QuitBtn = Button(
            (200, 50),
            (gameObject.screen.get_width() / 2, gameObject.screen.get_height() / 8 * 5 + 120),
            BUTTON_COLOR,
            Text("종료하기", button_font, Colors.WHITE),
            ButtonEvent(gameObject, lambda gameObject: gameObject.quit())
        )
        
        # element repositioning code
        # because of transition
        self.transitioning = True
        self.transitionEndTime = 1500
        
        standard_element = self.raws["score_splitted_time"]
        self.elementMoveLength = self.screen.get_height() - (standard_element[1][1] - standard_element[0].get_rect().height / 2)
        self.elementFinishPosition = standard_element[1][1]
        self.transitionMoveSpeed = self.elementMoveLength / self.transitionEndTime
        for key in self.raws:
            self.raws[key][1][1] += self.elementMoveLength
        
        # for star effect
        self.last_star_creation = data["lastStarCreation"]
    
    def update(self, events):
        # star effect
        if pg.time.get_ticks() - self.last_star_creation > star_effect_delay:
            self.add_item("stars", Star(randint(0, pg.display.get_window_size()[0]), randint(0, pg.display.get_window_size()[1])))
            self.last_star_creation = pg.time.get_ticks()
        # main update
        super().update(events)
        if self.transitioning:
            for key in self.raws:
                self.raws[key][1][1] -= self.transitionMoveSpeed
            if self.raws["score_splitted_time"][1][1] <= self.elementFinishPosition:
                self.transitioning = False
        else:
            from_last_time = pg.time.get_ticks() - self.last_update_time
            
            if not self.animation_finished:
                if not self.score_time_animation_finished:
                    if from_last_time >= self.score_animation_time_delay:
                        if self.anim_current_elapsed_time + self.score_animation_time_chunk > self.elapsed_time:
                            self.score_time_animation_finished = True
                            self.score_time_animation_finished_time = pg.time.get_ticks()
                            overflowed = self.score_animation_time_chunk - ((self.anim_current_elapsed_time + self.score_animation_time_chunk) - self.elapsed_time)
                            self.anim_current_elapsed_time += overflowed
                            self.anim_current_total_score += overflowed
                            self.last_update_time = pg.time.get_ticks()
                        else:
                            self.anim_current_elapsed_time += self.score_animation_time_chunk
                            self.anim_current_total_score += self.score_animation_time_chunk
                            self.last_update_time = pg.time.get_ticks()
                elif not self.score_barely_missed_animation_finished:
                    if from_last_time >= self.score_animation_barely_missed_delay:
                        if self.anim_current_score + self.score_animation_barely_missed_chunk > self.score:
                            self.score_barely_missed_animation_finished = True
                            self.score_barely_missed_animation_finished_time = pg.time.get_ticks()
                            overflowed = self.score_animation_barely_missed_chunk - ((self.anim_current_score + self.score_animation_barely_missed_chunk) - self.score)
                            self.anim_current_score += overflowed
                            self.anim_current_total_score += overflowed
                            self.last_update_time = pg.time.get_ticks()
                        else:
                            if pg.time.get_ticks() - self.score_time_animation_finished_time >= self.score_time_animation_finish_delay:
                                self.anim_current_score += self.score_animation_barely_missed_chunk
                                self.anim_current_total_score += self.score_animation_barely_missed_chunk
                                self.last_update_time = pg.time.get_ticks()
                else:
                    self.animation_finished = True
                    self.create_group("buttons", self.RestartBtn, self.MenuBtn, self.QuitBtn)
                    
            self.raws["score_displayer"][0] = self.score_displayer_font.render(f"{self.anim_current_total_score}", True, Colors.ORANGE.as_iter())
            
            self.raws["score_splitted_time"][0] = self.score_displayer_font.render(f"{self.anim_current_elapsed_time}", True, Colors.ORANGE.as_iter())
            
            self.raws["score_splitted_barely_missed"][0] = self.score_displayer_font.render(f"{self.anim_current_score}", True, Colors.ORANGE.as_iter())


class HowToPlayScene(Scene):
    def __init__(self, gameObject, data):
        super().__init__()
        self.screen_color = Colors.WHITE.as_iter()
        
        BUTTON_COLOR = [
            Colors.ORANGE,
            Colors.RED,
            Colors.RED - Color(100, 0, 0)
        ]
        button_font = pg.font.Font(font_located('ONE Mobile Bold'), 20)
        
        self.prevButton = Button((100, 25), 
                                 (80, gameObject.screen.get_height() - 80), 
                                 BUTTON_COLOR, 
                                 Text("이전", button_font, Colors.WHITE), 
                                 ButtonEvent(self, lambda howtoscene: howtoscene.prev_page()))
        self.nextButton = Button((100, 25), (gameObject.screen.get_width() - 80, gameObject.screen.get_height() - 80),
                                 BUTTON_COLOR,
                                 Text("다음", button_font, Colors.WHITE),
                                 ButtonEvent(self, lambda howtoscene: howtoscene.next_page()))
        self.quitHelpButton = Button((100, 25), 
                                     (gameObject.screen.get_width()-100, 50), 
                                     BUTTON_COLOR, 
                                     Text("메뉴로", button_font, Colors.WHITE), 
                                     ButtonEvent(gameObject, lambda gameObject: gameObject.change_scene(MenuScene)))
        
        self.page = 0
        
        self.fonts = {
            "title": pg.font.Font(font_located('ONE Mobile Title'), 50),
            "content": pg.font.Font(font_located('ONE Mobile Light'), 30)
        }
        self.page_elements = [
            [
                {
                    "type": "text",
                    "value": Text("게임 방법", self.fonts["title"], Colors.BLACK + Color(100, 100, 100), (gameObject.screen.get_width() / 2, 50), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("이 게임은 파란색 네모를 움직여", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (210, 150), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("빨간색 네모를 피하는 게임입니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (220, 220), TextShadowEffect(Colors.BLACK, (2,2))),
                }
            ],
            [
                {
                    "type": "text",
                    "value": Text("조작 방법", self.fonts["title"], Colors.BLACK + Color(100, 100, 100), (gameObject.screen.get_width() / 2, 50), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("W, A, S, D키로 움직입니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (190, 150), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("LSHIFT 키를 눌러 더욱 빠르게 움직일 수 있습니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (330, 220), TextShadowEffect(Colors.BLACK, (2,2))),
                }
            ],
            [
                {
                    "type": "text",
                    "value": Text("점수 방식", self.fonts["title"], Colors.BLACK + Color(100, 100, 100), (gameObject.screen.get_width() / 2, 50), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("MS 단위로 시간을 재 점수를 측정합니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (270, 150), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("시간은 가장 기본적인 점수입니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (220, 220), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("빨간색 네모를 피하면 점수가 잘 올라갑니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (280, 330), TextShadowEffect(Colors.BLACK, (2,2))),
                },
                {
                    "type": "text",
                    "value": Text("그것을 \"액션 점수\"라고 합니다.", self.fonts["content"], Colors.BLACK + Color(100, 100, 100), (200, 400), TextShadowEffect(Colors.BLACK, (2,2))),
                }
            ]
        ]
        self.current_page_elements = []
        self.create_group("currentPageElements")
        
    def update(self, events):
        super().update(events)
        if not self.current_page_elements:
            # init groups
            if "startPageButtons" in self.groups:
                del self.groups["startPageButtons"]
            if "middlePageButtons" in self.groups:
                del self.groups["middlePageButtons"]
            if "endPageButtons" in self.groups:
                del self.groups["endPageButtons"]
            
            if self.page == 0:
                self.create_group("startPageButtons", [self.nextButton, self.quitHelpButton])
            elif self.page == len(self.page_elements) - 1:
                self.create_group("endPageButtons", [self.prevButton, self.quitHelpButton])
            else:
                self.create_group("middlePageButtons", [self.prevButton, self.nextButton, self.quitHelpButton])
                    
            for element in self.page_elements[self.page]:
                self.add_item("currentPageElements", element["value"])
                
    
    def prev_page(self):
        self.page -= 1
        self.current_page_elements = []
        self.groups["currentPageElements"].empty()
    
    def next_page(self):
        self.page += 1
        self.current_page_elements = []
        self.groups["currentPageElements"].empty()