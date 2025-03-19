import pgzrun
import random
import sys

# Wndow size set to match our bg masterpiece (928 x 335)
WIDTH = 928
HEIGHT = 335
GAME_FLOOR = 255  # Floor lvl where our chars stand

# Basic stats – nothing fancy
MAX_HERO_HEALTH = 100
MAX_ENEMY_HEALTH = 50

# Global state vars – game_state can be "menu" or "playing"
game_state = "menu"
music_on = True  # initial music settng
wave_count = 1

# Menu buttons – start, toggle music (It doesnt shut off sound effects only bg soundtrack, which is an acoustic cover of Free Bird so why would you want to turn it off?), and exit
menu_buttons = [
    {"action": "start", "rect": Rect((WIDTH / 2 - 100, 100), (200, 40))},
    {"action": "toggle_music", "rect": Rect((WIDTH / 2 - 100, 160), (200, 40))},
    {"action": "exit", "rect": Rect((WIDTH / 2 - 100, 220), (200, 40))},
]


def spawn_wave():
    global enemies, wave_count
    enemies.clear()  # Clear out last wave's corpses – maybe remove this so you can see the carnage?
    num_enemies = 2 * wave_count  # Wave 1: 2 baddies, wave 2: 4, etc.
    print(f"[DEBUG] Spawning wave {wave_count} with {num_enemies} enemies")
    for i in range(num_enemies):
        # Try to spawn enemy far enough from the hero (avoid insta hugs)
        while True:
            x = random.randint(50, WIDTH - 50)
            if abs(x - player.actor.x) >= 100:
                break
        # Note to self: Skeleton asset is a bit shorter than knight, so adjust Y a bit.
        enemy = Enemy("skeleton", pos=(x, GAME_FLOOR + 23))
        enemies.append(enemy)


# Thsi Animation class is our way to make things move (or at least change imgs).
class Animation:
    def __init__(
        self,
        character_name,
        animation_name,
        tick_delay,
        retain_last_frame,
        loop=False,
        priority=5,
    ):
        self.character_name = character_name
        self.animation_name = animation_name
        self.tick_delay = tick_delay
        self.retain_last_frame = retain_last_frame
        self.loop = loop
        self.priority = priority
        self.frames = []
        self.load_frames()
        self.current_frame_index = 0
        self.tick_counter = 0
        self.finished = False

    def load_frames(self):
        frame = 0
        while True:
            frame_name = f"{self.character_name}_{self.animation_name}_{frame}"
            if hasattr(
                images, frame_name
            ):  ## my intellisense refuses to recognize images as a module
                self.frames.append(frame_name)
                frame += 1
            else:
                break
        if not self.frames:
            print(
                f"[DEBUG] No frames found for {self.character_name}_{self.animation_name}. (ugh!)"
            )
        else:
            print(
                f"[DEBUG] Loaded {len(self.frames)} frames for {self.character_name}_{self.animation_name}."
            )

    def update(self):
        if not self.frames:
            return None
        self.tick_counter += 1
        if self.tick_counter >= self.tick_delay:
            self.tick_counter = 0
            if self.current_frame_index < len(self.frames) - 1:
                self.current_frame_index += 1
            else:
                if self.loop:
                    self.current_frame_index = 0
                else:
                    self.finished = True
        return self.frames[self.current_frame_index]


# Base class for all our characters (hero and baddies)
class Character:
    def __init__(self, name, pos=(WIDTH // 2, HEIGHT // 2)):
        self.name = name
        self.health = MAX_HERO_HEALTH  # Default hero health; enemies will override
        self.alive = True
        self.pos = pos
        self.actor = Actor(name, pos)
        self.orientation = "right"  # Could be "left" too
        self.idle_animation = Animation(
            name, "idle", tick_delay=10, retain_last_frame=True, loop=True, priority=0
        )
        if not self.idle_animation.frames:
            self.idle_animation.frames = [name]
            print(f"[DEBUG] Using fallback idle image for {name}")
        self.animation_queue = []
        self.current_animation = None
        self.current_sound = None

    def play_animation_sound(self, animation):
        # Sounds need a lot of tune
        base_anim = (
            animation.animation_name.rsplit("_", 1)[0]
            if animation.animation_name.endswith("_right")
            or animation.animation_name.endswith("_left")
            else animation.animation_name
        )
        sound_name = f"{self.name}_{base_anim}"
        sound = getattr(
            sounds, sound_name, None
        )  ## my intellisense refuses to recognize sounds also !?
        if sound:
            if animation.animation_name.startswith("run_"):
                sound.play(loops=-1)
            else:
                sound.play()
            self.current_sound = sound
            print(f"[DEBUG] Playing sound: {sound_name}")
        else:
            print(f"[DEBUG] No sound found for: {sound_name}")

    def stop_current_sound(self):
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None

    def set_animation(self, new_animation):
        self.stop_current_sound()
        self.current_animation = new_animation
        self.play_animation_sound(new_animation)

    def run(self):
        run_priority = 5
        if self.current_animation and self.current_animation.priority > run_priority:
            return
        desired_animation = f"run_{self.orientation}"
        if (
            self.current_animation
            and self.current_animation.animation_name == desired_animation
        ):
            return
        self.animation_queue.clear()
        new_anim = Animation(
            self.name,
            desired_animation,
            tick_delay=3,
            retain_last_frame=False,
            loop=True,
            priority=run_priority,
        )
        self.set_animation(new_anim)
        print(f"[DEBUG] {self.name} is now running with {desired_animation}")

    def attack(self):
        # Always show the attack animation even if no enemy is hit.
        attack_priority = 10
        desired_animation = f"attack1_{self.orientation}"
        self.animation_queue.clear()
        new_anim = Animation(
            self.name,
            desired_animation,
            tick_delay=5,
            retain_last_frame=True,
            loop=False,
            priority=attack_priority,
        )
        self.set_animation(new_anim)
        print(f"[DEBUG] {self.name} attacks with {desired_animation}")

    def die(self):
        if not self.alive:
            return
        self.alive = False
        self.animation_queue.clear()
        self.stop_current_sound()
        death_anim = Animation(
            self.name,
            "death",
            tick_delay=10,
            retain_last_frame=True,
            loop=False,
            priority=10,
        )
        self.set_animation(death_anim)
        print(f"[DEBUG] {self.name} is dying...")

    def update_animation(self):
        if not self.current_animation and self.animation_queue:
            self.current_animation = self.animation_queue.pop(0)
            self.play_animation_sound(self.current_animation)
        if self.current_animation:
            frame = self.current_animation.update()
            if frame:
                self.actor.image = frame
            if self.current_animation.finished:
                print(
                    f"[DEBUG] {self.name} finished {self.current_animation.animation_name}"
                )
                self.stop_current_sound()
                self.current_animation = None
        else:
            if self.alive:
                frame = self.idle_animation.update()
                if frame:
                    self.actor.image = frame


# Enemy subclass (skeleton) – simple, but it gets the job done.
class Enemy(Character):
    def __init__(self, name, pos=(WIDTH // 2, HEIGHT // 2)):
        super().__init__(name, pos)
        self.health = MAX_ENEMY_HEALTH
        self.attack_cooldown = 0  # Time until next attack
        self.attacking = False

    def attack(self):
        attack_priority = 10
        desired_animation = f"attack_{self.orientation}"
        self.animation_queue.clear()
        new_anim = Animation(
            self.name,
            desired_animation,
            tick_delay=5,
            retain_last_frame=True,
            loop=False,
            priority=attack_priority,
        )
        self.set_animation(new_anim)
        print(f"[DEBUG] {self.name} attacks with {desired_animation}")
        # Damage is applied after the animation finishes.

    def interrupt_attack(self):
        if self.attacking:
            print(
                f"[DEBUG] {self.name}'s attack got interrupted by the hero (eat that?)"
            )
            self.attacking = False
            self.animation_queue.clear()
            if (
                self.current_animation
                and self.current_animation.animation_name.startswith("attack")
            ):
                self.current_animation = None
            self.attack_cooldown = 30

    def update_ai(self, target):
        if not self.alive or not target.alive:
            return
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        attack_range = 50
        damage = 20
        knockback_amount = 10
        if self.attacking and not self.current_animation:
            if abs(self.actor.x - target.actor.x) <= attack_range:
                target.health -= damage
                if self.orientation == "right":
                    target.actor.x -= knockback_amount
                else:
                    target.actor.x += knockback_amount
                print(f"[DEBUG] {self.name} hit {target.name} for {damage} HP!")
                if target.health <= 0:
                    target.die()
            else:
                print(f"[DEBUG] {self.name}'s attack missed")
            self.attacking = False
            self.attack_cooldown = 60
            return
        if not self.attacking:
            if abs(self.actor.x - target.actor.x) > attack_range:
                if self.actor.x < target.actor.x:
                    self.orientation = "right"
                    self.actor.x += 1
                else:
                    self.orientation = "left"
                    self.actor.x -= 1
                self.run()
            else:
                if self.attack_cooldown == 0:
                    self.attacking = True
                    self.attack()


# Our hero (knight) – dashing, attacking, and just plain cool.
class Hero(Character):
    def __init__(self, name, pos=(WIDTH // 2, HEIGHT // 2)):
        super().__init__(name, pos)
        self.stamina = 100
        self.max_stamina = 100
        self.dash_cooldown = 0  # Frames before another dash is allowed
        self.is_dashing = False
        self.dash_start_x = 0
        self.dash_target_x = 0
        self.dash_duration = 10  # Dash lasts 10 frames – blink and you'll miss it!
        self.dash_timer = 0

    def attack(self):
        # Always show the attack animation even if no enemy is hit.
        attack_cost = 20
        if self.stamina < attack_cost:
            print("[DEBUG] Not enough stamina to attack")
            return
        self.stamina -= attack_cost
        super().attack()
        attack_range = 50
        damage = 20
        knockback_amount = 10
        target = None
        for enemy in enemies:
            if enemy.alive:
                if (
                    self.orientation == "right"
                    and enemy.actor.x > self.actor.x
                    and abs(enemy.actor.x - self.actor.x) <= attack_range
                ):
                    if not target or abs(enemy.actor.x - self.actor.x) < abs(
                        target.actor.x - self.actor.x
                    ):
                        target = enemy
                elif (
                    self.orientation == "left"
                    and enemy.actor.x < self.actor.x
                    and abs(enemy.actor.x - self.actor.x) <= attack_range
                ):
                    if not target or abs(enemy.actor.x - self.actor.x) < abs(
                        target.actor.x - self.actor.x
                    ):
                        target = enemy
        if target:
            target.health -= damage
            if self.orientation == "right":
                target.actor.x += knockback_amount
            else:
                target.actor.x -= knockback_amount
            print(
                f"[DEBUG] {self.name} hit {target.name} for {damage} HP with a  knockback!"
            )
            if target.health <= 0:
                target.die()
            if target.attacking:
                target.interrupt_attack()

    def dash(self):
        # Dash consumes stamina – gotta spend some energy to be fast!
        dash_cost = 20
        if self.dash_cooldown > 0 or self.is_dashing or self.stamina < dash_cost:
            return
        self.stamina -= dash_cost
        dash_distance = 150
        self.dash_start_x = self.actor.x
        self.dash_target_x = (
            self.actor.x + dash_distance
            if self.orientation == "right"
            else self.actor.x - dash_distance
        )
        self.dash_duration = 10  # A quick burst over 10 frames
        self.dash_timer = 0
        self.is_dashing = True
        desired_animation = f"dash_{self.orientation}"
        self.animation_queue.clear()
        # Set the dash animation to loop only during the dash period.
        dash_anim = Animation(
            self.name,
            desired_animation,
            tick_delay=3,
            retain_last_frame=False,
            loop=True,
            priority=15,
        )
        self.set_animation(dash_anim)
        print(f"[DEBUG] {self.name} started a dash to the {self.orientation}")


# Create our hero (Named Niyazi) and spawn the first wave
player = Hero("knight", pos=(WIDTH // 2, GAME_FLOOR))
enemies = []
spawn_wave()


def draw_menu():
    for btn in menu_buttons:
        if btn["action"] == "toggle_music":
            text = "Music: On" if music_on else "Music: Off"
        else:
            text = btn["action"].capitalize() if btn["action"] != "exit" else "Exit"
            if btn["action"] == "start":
                text = "Start"
        screen.draw.filled_rect(btn["rect"], "gray")
        screen.draw.rect(btn["rect"], "white")
        screen.draw.text(text, center=btn["rect"].center, color="white", fontsize=30)


def draw():
    # Always show our gorgeous background. https://edermunizz.itch.io/free-pixel-art-forest
    screen.blit("background", (0, 0))
    if game_state == "playing":
        player.actor.draw()
        for enemy in enemies:
            enemy.actor.draw()
        margin = 10
        bar_width = 200
        bar_height = 20
        x = WIDTH - bar_width - margin
        y = margin
        screen.draw.rect(Rect((x, y), (bar_width, bar_height)), "white")
        health_width = int((player.health / MAX_HERO_HEALTH) * bar_width)
        screen.draw.filled_rect(Rect((x, y), (health_width, bar_height)), "green")
        stamina_y = y + bar_height + 5
        screen.draw.rect(Rect((x, stamina_y), (bar_width, bar_height)), "white")
        stamina_width = int((player.stamina / player.max_stamina) * bar_width)
        screen.draw.filled_rect(
            Rect((x, stamina_y), (stamina_width, bar_height)), "blue"
        )
        screen.draw.text(
            f"Wave: {wave_count}", (margin, margin), color="white", fontsize=30
        )
        if not player.alive:
            screen.draw.text(
                "GAME OVER", center=(WIDTH // 2, HEIGHT // 2), color="red", fontsize=60
            )
    elif game_state == "menu":
        draw_menu()


def update():
    global wave_count, game_state
    if game_state == "playing":
        if player.alive:
            if not player.is_dashing:
                moved = False
                if keyboard.left or keyboard.a:
                    player.orientation = "left"
                    player.actor.x -= 2
                    moved = True
                elif keyboard.right or keyboard.d:
                    player.orientation = "right"
                    player.actor.x += 2
                    moved = True

                if moved:
                    player.run()
                else:
                    if (
                        player.current_animation
                        and player.current_animation.animation_name.startswith("run_")
                    ):
                        player.current_animation = None
                        player.animation_queue.clear()
                        player.stop_current_sound()

                if keyboard.space:
                    player.dash()
            else:
                progress = player.dash_timer / player.dash_duration
                player.actor.x = player.dash_start_x + progress * (
                    player.dash_target_x - player.dash_start_x
                )
                player.dash_timer += 1
                if player.dash_timer >= player.dash_duration:
                    player.is_dashing = False
                    player.dash_cooldown = 60
                    player.current_animation = None

            if player.stamina < player.max_stamina:
                player.stamina = min(player.max_stamina, player.stamina + 1)
        if player.dash_cooldown > 0:
            player.dash_cooldown = max(0, player.dash_cooldown - 1)

        player.update_animation()
        for enemy in enemies:
            enemy.update_ai(player)
            enemy.update_animation()
        if player.alive and enemies and not any(enemy.alive for enemy in enemies):
            wave_count += 1
            spawn_wave()
    elif game_state == "menu":
        # Just chill in the menu until someone clicks a button.
        pass


def on_mouse_down(pos, button):
    global game_state, music_on
    if game_state == "menu":
        for btn in menu_buttons:
            if btn["rect"].collidepoint(pos):
                action = btn["action"]
                if action == "start":
                    game_state = "playing"
                    if music_on:
                        sounds.soundtrack.play(loops=-1)
                elif action == "toggle_music":
                    if music_on:
                        sounds.soundtrack.stop()
                        music_on = False
                    else:
                        if game_state == "playing":
                            sounds.soundtrack.play(loops=-1)
                        music_on = True
                elif action == "exit":
                    sys.exit()
    elif game_state == "playing":
        if button == mouse.LEFT and player.alive:
            player.attack()


pgzrun.go()
