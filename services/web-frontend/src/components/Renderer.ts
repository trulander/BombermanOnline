import logger, { LogLevel } from '../utils/Logger';
import {GameState} from "../types/Game";
import { EntitiesInfo, EntityInfo, UnitInfo } from '../types/EntitiesParams';
import { EnemyType, PowerUpType, WeaponType } from '../types/Game';

export class Renderer {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private cellSize: number = 40;
    
    // Добавляем дополнительные переменные для плавного перемещения
    private currentMapOffset = { x: 0, y: 0 };
    private targetMapOffset = { x: 0, y: 0 };
    private previousFrameTime: number = 0;
    
    // Размеры видимой области карты (фактический размер рендера)
    private viewWidth: number = 0;
    private viewHeight: number = 0;
    
    // Размер видимой области в клетках (для определения зоны видимости)
    private viewRadius: number = 6;
    
    // Размер "мёртвой зоны" - области, в которой игрок может двигаться без смещения карты
    private deadZoneSize = {
        width: 100,  // пикселей
        height: 100  // пикселей
    };
    
    // Флаг для отладки
    private debugMode: boolean = false;
    
    private entitiesInfo: EntitiesInfo;

    constructor(
        canvas: HTMLCanvasElement,
        entitiesInfo: EntitiesInfo
    ) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d')!;
        this.previousFrameTime = performance.now();
        this.entitiesInfo = entitiesInfo;
        
        // Установка начальных размеров canvas
        this.canvas.width = 800;
        this.canvas.height = 600;
    }

    public render(gameState: GameState, currentPlayerId: string | null): void {
        const currentTime = performance.now();
        const deltaTime = (currentTime - this.previousFrameTime) / 2;
        this.previousFrameTime = currentTime;
        
        // Проверяем наличие необходимых данных
        if (!gameState.map || !gameState.map.grid) {
            logger.error('Отсутствует gameState.map.grid_data', {
                gameState: gameState,
                time: currentTime
            });
            this.renderErrorMessage('Ошибка: данные карты отсутствуют');
            return;
        }
        
        if (!currentPlayerId || !gameState.players[currentPlayerId]) {
            logger.error('Отсутствует текущий игрок', {
                currentPlayerId,
                gameState: gameState,
                time: currentTime
            });
            this.renderErrorMessage('Ошибка: данные игрока отсутствуют');
            return;
        }
        
        // Получаем текущего игрока
        const currentPlayer = gameState.players[currentPlayerId];
        
        // Логируем данные для отладки
        if (this.debugMode) {
            logger.debug('Рендер кадра', {
                cellSize: this.cellSize,
                playerPos: { x: currentPlayer.x, y: currentPlayer.y },
                gridSize: {
                    width: gameState.map.width,
                    height: gameState.map.height
                },
                time: currentTime
            });
        }

        // Вычисляем смещение вида на основе положения игрока и мёртвой зоны
        const viewOffset = this.calculateViewOffsetWithDeadZone(
            currentPlayer.x, 
            currentPlayer.y, 
            gameState.map
        );
        
        // Устанавливаем целевое смещение карты
        this.targetMapOffset.x = viewOffset.x;
        this.targetMapOffset.y = viewOffset.y;
        
        // Плавно перемещаем текущее смещение к целевому
        // Уменьшаем скорость интерполяции для плавности движения
        const lerpFactor = Math.min(1, deltaTime * 3.5);
        
        // Добавляем более плавную интерполяцию с уменьшением скорости при приближении к цели
        const distanceX = this.targetMapOffset.x - this.currentMapOffset.x;
        const distanceY = this.targetMapOffset.y - this.currentMapOffset.y;
        const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
        
        // Если расстояние до цели очень маленькое, замедляем движение еще больше
        let adaptiveLerpFactor = lerpFactor;
        if (distance < 10) {
            adaptiveLerpFactor = lerpFactor * (distance / 10); // Плавно уменьшаем скорость
        }
        
        // Если расстояние совсем малое, просто устанавливаем точное значение
        if (distance < 0.1) {
            this.currentMapOffset.x = this.targetMapOffset.x;
            this.currentMapOffset.y = this.targetMapOffset.y;
        } else {
            this.currentMapOffset.x += distanceX * adaptiveLerpFactor;
            this.currentMapOffset.y += distanceY * adaptiveLerpFactor;
        }
        
        // Определяем размер видимой области для отображения
        this.viewWidth = (this.viewRadius * 2 + 1) * this.cellSize;
        this.viewHeight = (this.viewRadius * 2 + 1) * this.cellSize;
        
        // Убеждаемся, что размер canvas соответствует размеру видимой области
        if (this.canvas.width !== this.viewWidth || this.canvas.height !== this.viewHeight) {
            logger.debug(`Изменение размера canvas`, {
                oldWidth: this.canvas.width,
                oldHeight: this.canvas.height,
                newWidth: this.viewWidth,
                newHeight: this.viewHeight
            });
            this.canvas.width = this.viewWidth;
            this.canvas.height = this.viewHeight;
        }

        // Очищаем canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Вычисляем разницу между целевым и текущим смещением для корректировки координат
        const offsetDiffX = this.targetMapOffset.x - this.currentMapOffset.x;
        const offsetDiffY = this.targetMapOffset.y - this.currentMapOffset.y;
        
        // Рендерим фон (сетка) для всей видимой области
        this.renderBackground();
        
        // Рендерим игровые объекты с учетом плавного смещения
        this.renderMapSection(gameState, this.currentMapOffset.x, this.currentMapOffset.y, offsetDiffX, offsetDiffY);
        this.renderPowerUps(gameState, offsetDiffX, offsetDiffY);
        this.renderWeapons(gameState, offsetDiffX, offsetDiffY);
        this.renderEnemies(gameState, offsetDiffX, offsetDiffY);
        this.renderPlayers(gameState, currentPlayerId, offsetDiffX, offsetDiffY);

        // Рендерим обратный таймер если он активен
        this.renderTimer(gameState);

        // Рендерим отладочную информацию
        if (this.debugMode) {
            this.renderDebugInfo(gameState, currentPlayerId, offsetDiffX, offsetDiffY);
        }
    }
    
    // Остальные методы рендеринга и вспомогательные функции (выборочно)
    
    private renderBackground(): void {
        // Рисуем простую сетку для фона
        this.ctx.fillStyle = "#3c3c3c";
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Рисуем линии сетки
        this.ctx.strokeStyle = "#4a4a4a";
        this.ctx.lineWidth = 1;
        
        // Вертикальные линии
        for (let x = 0; x <= this.canvas.width; x += this.cellSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        
        // Горизонтальные линии
        for (let y = 0; y <= this.canvas.height; y += this.cellSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
    }
    
    private calculateViewOffsetWithDeadZone(playerX: number, playerY: number, map: GameState['map']): { x: number, y: number } {
        if (!map || !map.width || !map.height || !map.grid) {
            logger.error('Недостаточно данных для расчета смещения вида', {
                map,
                playerX,
                playerY
            });
            return { x: 0, y: 0 };
        }
        
        // Центр экрана
        const viewCenterX = this.viewWidth / 2;
        const viewCenterY = this.viewHeight / 2;
        
        // Для первого вызова используем поцизию игрока, центрированную на экране
        if (this.currentMapOffset.x === 0 && this.currentMapOffset.y === 0) {
            // Вычисляем начальное смещение, чтобы центрировать игрока
            const initialX = Math.max(0, playerX - viewCenterX);
            const initialY = Math.max(0, playerY - viewCenterY);
            
            logger.debug('Инициализация начального смещения', { 
                x: initialX,
                y: initialY,
                playerX,
                playerY
            });
            
            // Сразу устанавливаем текущее смещение
            this.currentMapOffset.x = initialX;
            this.currentMapOffset.y = initialY;
            
            return { x: initialX, y: initialY };
        }
        
        // Текущая позиция игрока относительно видимой области
        const playerViewX = playerX - this.currentMapOffset.x;
        const playerViewY = playerY - this.currentMapOffset.y;
        
        // Смещение игрока от центра
        const deltaX = playerViewX - viewCenterX;
        const deltaY = playerViewY - viewCenterY;
        
        // Новое смещение карты - двигаем только если игрок вышел из мёртвой зоны
        let newOffsetX = this.currentMapOffset.x;
        let newOffsetY = this.currentMapOffset.y;
        
        // Проверяем, вышел ли игрок за пределы мёртвой зоны по X
        if (Math.abs(deltaX) > this.deadZoneSize.width / 2) {
            // Определяем, насколько игрок вышел за пределы мёртвой зоны
            const exceedX = Math.abs(deltaX) - this.deadZoneSize.width / 2;
            // Добавляем плавное увеличение смещения
            const factorX = Math.min(1, exceedX / 30); // Постепенно увеличиваем до 1
            // Смещаем карту в том же направлении, что и движение игрока
            newOffsetX += exceedX * Math.sign(deltaX) * factorX;
        }
        
        // Проверяем, вышел ли игрок за пределы мёртвой зоны по Y
        if (Math.abs(deltaY) > this.deadZoneSize.height / 2) {
            // Определяем, насколько игрок вышел за пределы мёртвой зоны
            const exceedY = Math.abs(deltaY) - this.deadZoneSize.height / 2;
            // Добавляем плавное увеличение смещения
            const factorY = Math.min(1, exceedY / 30); // Постепенно увеличиваем до 1
            // Смещаем карту в том же направлении, что и движение игрока
            newOffsetY += exceedY * Math.sign(deltaY) * factorY;
        }
        
        // Проверка и ограничение границ карты
        if (map.width && map.height) {
            // Максимальные значения смещения (размер полной карты минус размер видимой области)
            const maxOffsetX = Math.max(0, map.width * this.cellSize - this.viewWidth);
            const maxOffsetY = Math.max(0, map.height * this.cellSize - this.viewHeight);
            
            // Ограничиваем смещение, чтобы карта не выходила за границы
            newOffsetX = Math.max(0, Math.min(maxOffsetX, newOffsetX));
            newOffsetY = Math.max(0, Math.min(maxOffsetY, newOffsetY));
        }
        
        return { x: newOffsetX, y: newOffsetY };
    }
    
    private calculateViewOffset(playerX: number, playerY: number, map: GameState['map']): { x: number, y: number } {
        if (!map || !map.width || !map.height) {
            return { x: 0, y: 0 };
        }

        // Преобразуем координаты игрока в координаты сетки
        const gridX = Math.floor(playerX / this.cellSize);
        const gridY = Math.floor(playerY / this.cellSize);

        // Определяем размер видимой области (по viewRadius клеток в каждую сторону от игрока)
        const viewWidth = this.viewRadius * 2 + 1;
        const viewHeight = this.viewRadius * 2 + 1;

        // Вычисляем начальные координаты видимой области
        let startX = Math.max(0, Math.min(map.width - viewWidth, gridX - this.viewRadius));
        let startY = Math.max(0, Math.min(map.height - viewHeight, gridY - this.viewRadius));

        // Вычисляем смещение видимой области относительно начала карты в пикселях
        return {
            x: startX * this.cellSize,
            y: startY * this.cellSize
        };
    }

    private renderMapSection(gameState: GameState, offsetX: number, offsetY: number, offsetDiffX: number, offsetDiffY: number): void {
        const map = gameState.map;
        if (!map || !map.grid) {
            logger.error('Отсутствует gameState.map.grid_data при рендеринге карты', {
                gameState
            });
            return;
        }
        
        // Вычисляем границы видимой области в координатах сетки
        const startGridX = Math.floor(offsetX / this.cellSize);
        const startGridY = Math.floor(offsetY / this.cellSize);
        const endGridX = Math.min(map.width || map.grid[0].length, startGridX + (this.viewRadius * 2 + 1) + 1);
        const endGridY = Math.min(map.height || map.grid.length, startGridY + (this.viewRadius * 2 + 1) + 1);

        // Рендерим только видимую часть карты
        for (let y = startGridY; y < endGridY; y++) {
            for (let x = startGridX; x < endGridX; x++) {
                if (x < 0 || y < 0 || y >= map.grid.length || x >= map.grid[0].length) continue;
                
                const cellType = map.grid[y] && map.grid[y][x] !== undefined ? map.grid[y][x] : 0;
                
                // Вычисляем координаты ячейки с учетом плавного смещения
                const renderX = (x * this.cellSize) - offsetX + offsetDiffX;
                const renderY = (y * this.cellSize) - offsetY + offsetDiffY;

                switch (cellType) {
                    case 0: // Empty
                        this.ctx.fillStyle = "#8CBF26"; // Green grass
                        break;
                    case 1: // Solid wall
                        this.ctx.fillStyle = "#6B6B6B"; // Dark gray
                        break;
                    case 2: // Breakable block
                        this.ctx.fillStyle = "#B97A57"; // Brown
                        break;
                    default:
                        this.ctx.fillStyle = "#FF00FF"; // Magenta для неизвестного типа
                        logger.debug(`Неизвестный тип ячейки`, {
                            cellType,
                            x,
                            y
                        });
                        break;
                }

                this.ctx.fillRect(renderX, renderY, this.cellSize, this.cellSize);

                // Add visual details
                if (cellType === 1) { // Solid wall
                    this.ctx.strokeStyle = "#555555";
                    this.ctx.lineWidth = 2;
                    this.ctx.strokeRect(
                        renderX + 2,
                        renderY + 2,
                        this.cellSize - 4,
                        this.cellSize - 4
                    );
                } else if (cellType === 2) { // Breakable block
                    this.ctx.fillStyle = "#8E5E42";
                    this.ctx.fillRect(
                        renderX + this.cellSize / 4,
                        renderY + this.cellSize / 4,
                        this.cellSize / 2,
                        this.cellSize / 2
                    );
                }
            }
        }
    }
    
    private renderPowerUps(gameState: GameState, offsetDiffX: number, offsetDiffY: number): void {
        if (!gameState.power_ups) return;

        for (const powerUpId in gameState.power_ups) {
            const powerUp = gameState.power_ups[powerUpId];
            // Get dimensions from entitiesInfo
            const powerUpInfo = this.entitiesInfo.power_up_types[powerUp.type];
            const width = powerUpInfo?.width || this.cellSize;
            const height = powerUpInfo?.height || this.cellSize;

            // Проверяем, находится ли powerUp в видимой области
            if (!this.isObjectVisible(powerUp.x, powerUp.y, width, height)) continue;
            
            // Floating animation
            const time = performance.now() / 1000;
            const floatOffset = Math.sin(time * 3) * 3;

            // Get color based on type
            let color = "#9B59B6"; // Default purple
            let shadowColor = "rgba(155, 89, 182, 0.7)";
            let symbol = "?";

            switch (powerUp.type as PowerUpType) {
                case PowerUpType.BOMB_UP:
                    color = "#F39C12"; // Orange
                    shadowColor = "rgba(243, 156, 18, 0.7)";
                    symbol = "BU";
                    break;
                case PowerUpType.BULLET_UP:
                    color = "#E74C3C"; // Red
                    shadowColor = "rgba(231, 76, 60, 0.7)";
                    symbol = "BU";
                    break;
                case PowerUpType.MINE_UP:
                    color = "#E74C3C"; // Red
                    shadowColor = "rgba(231, 76, 60, 0.7)";
                    symbol = "MU";
                    break;
                case PowerUpType.BOMB_POWER_UP:
                    color = "#E74C3C"; // Red
                    shadowColor = "rgba(231, 76, 60, 0.7)";
                    symbol = "BPU";
                    break;
                case PowerUpType.BULLET_POWER_UP:
                    color = "#E74C3C"; // Red
                    shadowColor = "rgba(231, 76, 60, 0.7)";
                    symbol = "BPU";
                    break;
                case PowerUpType.LIFE_UP:
                    color = "#3498DB"; // Blue
                    shadowColor = "rgba(52, 152, 219, 0.7)";
                    symbol = "♥";
                    break;
                case PowerUpType.SPEED_UP:
                    color = "#2ECC71"; // Green
                    shadowColor = "rgba(46, 204, 113, 0.7)";
                    symbol = ">>";
                    break;
                default:
                    logger.warn(`Неизвестный тип бонуса`, { type: powerUp.type });
                    break;
            }

            // Draw power-up with glow
            this.ctx.shadowColor = shadowColor;
            this.ctx.shadowBlur = 10;

            // Draw base with correct position
            this.ctx.fillStyle = color;
            const renderX = this.getRelativeX(powerUp.x) + offsetDiffX;
            const renderY = this.getRelativeY(powerUp.y + floatOffset) + offsetDiffY;

            this.ctx.beginPath();
            this.ctx.arc(
                renderX + this.cellSize / 2,
                renderY + this.cellSize / 2,
                width / 2,
                0,
                Math.PI * 2
            );
            this.ctx.fill();

            // Draw icon
            this.ctx.fillStyle = "white";
            this.ctx.font = `bold ${width / 2}px Arial`;
            this.ctx.textAlign = "center";
            this.ctx.textBaseline = "middle";
            this.ctx.fillText(symbol, renderX + width / 2, renderY + height / 2);

            // Reset shadow
            this.ctx.shadowBlur = 0;
        }
    }

    private renderWeapons(gameState: GameState, offsetDiffX: number, offsetDiffY: number): void {
        if (!gameState.weapons) return;

        for (const weaponId in gameState.weapons) {
            const weapon = gameState.weapons[weaponId];
            // Get dimensions from entitiesInfo for the specific weapon type
            const weaponInfo = this.entitiesInfo.weapon_types[weapon.weapon_type];
            const width = weaponInfo?.width || this.cellSize;
            const height = weaponInfo?.height || this.cellSize;

            // Filter for bombs and render
            if (weapon.weapon_type === WeaponType.BOMB) {
                if (!weapon.activated && !this.isObjectVisible(weapon.x, weapon.y, width, height)) continue;

                if (!weapon.activated) {
                    // Bomb pulsating effect
                    const time = performance.now() / 1000;
                    const scale = 0.8 + Math.sin(time * 5) * 0.1;
                    const size = (width + height) / 2;
                    const offset = (this.cellSize - size) / 2;

                    // Draw bomb with smooth movement
                    const renderX = this.getRelativeX(weapon.x) + offsetDiffX;
                    const renderY = this.getRelativeY(weapon.y) + offsetDiffY;

                    this.ctx.fillStyle = "#333";
                    this.ctx.beginPath();
                    this.ctx.arc(
                        renderX + this.cellSize / 2,
                        renderY + this.cellSize / 2,
                        size / 2,
                        0,
                        Math.PI * 2
                    );
                    this.ctx.fill();

                    // Draw fuse
                    this.ctx.strokeStyle = "#999";
                    this.ctx.lineWidth = 2;
                    this.ctx.beginPath();
                    this.ctx.moveTo(renderX + this.cellSize / 2, renderY + offset);
                    this.ctx.lineTo(renderX + this.cellSize / 2, renderY - 5);
                    this.ctx.stroke();
                } else {
                    // Draw explosion with smooth movement
                    for (const cell of weapon.explosion_cells) {
                        const counted_x: number = cell[0] * this.cellSize
                        const counted_y: number = cell[1] * this.cellSize
                        if (!this.isObjectVisible(counted_x, counted_y, this.cellSize, this.cellSize)) continue;
                        const expRenderX = this.getRelativeX(counted_x) + offsetDiffX;
                        const expRenderY = this.getRelativeY(counted_y) + offsetDiffY;
                        
                        // Explosion gradient
                        const gradient = this.ctx.createRadialGradient(
                            expRenderX + this.cellSize / 2,
                            expRenderY + this.cellSize / 2,
                            0,
                            expRenderX + this.cellSize / 2,
                            expRenderY + this.cellSize / 2,
                            this.cellSize / 2
                        );

                        gradient.addColorStop(0, "rgba(255, 255, 0, 0.8)");
                        gradient.addColorStop(0.7, "rgba(255, 80, 0, 0.8)");
                        gradient.addColorStop(1, "rgba(255, 0, 0, 0.4)");

                        this.ctx.fillStyle = gradient;
                        this.ctx.fillRect(expRenderX, expRenderY, this.cellSize, this.cellSize);
                    }
                }
            } else if (weapon.weapon_type === WeaponType.BULLET) {
                // Render bullets (example - similar to power-ups or smaller circles)
                if (!this.isObjectVisible(weapon.x, weapon.y, width, height)) continue;

                const renderX = this.getRelativeX(weapon.x) + offsetDiffX;
                const renderY = this.getRelativeY(weapon.y) + offsetDiffY;

                this.ctx.fillStyle = "#8B0000"; // Dark red for bullets
                this.ctx.beginPath();
                this.ctx.arc(
                    renderX + this.cellSize / 2,
                    renderY + this.cellSize / 2,
                    width / 2,
                    0,
                    Math.PI * 2
                );
                this.ctx.fill();
            } else if (weapon.weapon_type === WeaponType.MINE) {
                // Render mines (example)
                if (!weapon.activated && !this.isObjectVisible(weapon.x, weapon.y, width, height)) continue;
                
                const renderX = this.getRelativeX(weapon.x) + offsetDiffX;
                const renderY = this.getRelativeY(weapon.y) + offsetDiffY;

                this.ctx.fillStyle = "#4B0082"; // Indigo for mines
                this.ctx.fillRect(renderX, renderY, width, height);

                if (!weapon.activated) {
                    this.ctx.strokeStyle = "#fff";
                    this.ctx.lineWidth = 1;
                    this.ctx.strokeRect(renderX + 2, renderY + 2, width - 4, height - 4);
                } else {
                    // Explosion rendering for mine (can reuse bomb explosion logic or simplify)
                    for (const cell of weapon.explosion_cells) {
                        const counted_x: number = cell[0] * this.cellSize
                        const counted_y: number = cell[1] * this.cellSize
                        if (!this.isObjectVisible(counted_x, counted_y, this.cellSize, this.cellSize)) continue;
                        const expRenderX = this.getRelativeX(counted_x) + offsetDiffX;
                        const expRenderY = this.getRelativeY(counted_y) + offsetDiffY;
                        this.ctx.fillStyle = "rgba(255, 140, 0, 0.6)"; // Orange for mine explosion
                        this.ctx.fillRect(expRenderX, expRenderY, this.cellSize, this.cellSize);
                    }
                }
            }
        }
    }

    private renderEnemies(gameState: GameState, offsetDiffX: number, offsetDiffY: number): void {
        if (!gameState.enemies) return;

        for (const enemyId in gameState.enemies) {
            const enemy = gameState.enemies[enemyId];
            if (enemy.destroyed) continue; // Don't render destroyed enemies

            // Get dimensions from entitiesInfo
            const enemyInfo = this.entitiesInfo.enemy_types[enemy.type];
            const width = enemyInfo?.width || this.cellSize;
            const height = enemyInfo?.height || this.cellSize;

            // Проверяем, находится ли враг в видимой области
            if (!this.isObjectVisible(enemy.x, enemy.y, width, height)) continue;

            // Apply smooth movement
            const renderX = this.getRelativeX(enemy.x) + offsetDiffX;
            const renderY = this.getRelativeY(enemy.y) + offsetDiffY;

            const centerX = renderX + this.cellSize / 2;
            const centerY = renderY + this.cellSize / 2;

            // Draw based on type
            switch (enemy.type as EnemyType) {
                case EnemyType.COIN:
                    this.ctx.fillStyle = "#FFD700"; // Gold
                    this.ctx.beginPath();
                    this.ctx.arc(centerX, centerY, width / 2, 0, Math.PI * 2);
                    this.ctx.fill();
                    // Add a simple shine effect
                    this.ctx.fillStyle = "#FFFFE0"; // Light yellow
                    this.ctx.beginPath();
                    this.ctx.arc(centerX - width * 0.15, centerY - height * 0.15, width / 5, 0, Math.PI * 2);
                    this.ctx.fill();
                    break;
                case EnemyType.BEAR:
                    this.ctx.fillStyle = "#8B4513"; // SaddleBrown
                    this.ctx.fillRect(renderX, renderY, width, height);
                    // Simple ears
                    this.ctx.fillStyle = "#A0522D"; // Sienna
                    this.ctx.beginPath();
                    this.ctx.arc(renderX + width * 0.25, renderY, width / 4, Math.PI, Math.PI * 2);
                    this.ctx.arc(renderX + width * 0.75, renderY, width / 4, Math.PI, Math.PI * 2);
                    this.ctx.fill();
                    // Simple eyes
                    this.ctx.fillStyle = "#000";
                    const bearEyeSize = width / 8;
                    this.ctx.fillRect(renderX + width * 0.2, renderY + height * 0.3, bearEyeSize, bearEyeSize);
                    this.ctx.fillRect(renderX + width * 0.6, renderY + height * 0.3, bearEyeSize, bearEyeSize);
                    break;
                case EnemyType.GHOST:
                    // Semi-transparent ghost
                    this.ctx.fillStyle = "rgba(200, 200, 255, 0.8)";

                    // Ghost body (rounded top)
                    this.ctx.beginPath();
                    this.ctx.arc(renderX + width / 2, renderY + height / 3, width / 2, Math.PI, 0, true);
                    this.ctx.lineTo(renderX + width, renderY + height);

                    // Wavy bottom
                    const waveCount = 3;
                    const waveWidth = width / waveCount;
                    for (let i = 0; i < waveCount; i++) {
                        this.ctx.arc(
                            renderX + width - (i * waveWidth) - waveWidth / 2,
                            renderY + height,
                            waveWidth / 2,
                            0,
                            Math.PI,
                            false
                        );
                    }

                    this.ctx.lineTo(renderX, renderY + height / 3);
                    this.ctx.fill();

                    // Eyes
                    this.ctx.fillStyle = "#000";
                    this.ctx.beginPath();
                    this.ctx.arc(renderX + width * 0.3, renderY + height * 0.4, width / 10, 0, Math.PI * 2);
                    this.ctx.arc(renderX + width * 0.7, renderY + height * 0.4, width / 10, 0, Math.PI * 2);
                    this.ctx.fill();
                    break;
                default:
                    logger.warn(`Неизвестный тип врага`, { type: enemy.type });
                    // Default enemy (simple square)
                    this.ctx.fillStyle = "#FF6B6B";
                    this.ctx.fillRect(renderX, renderY, width, height);
                    break;
            }
            
            // Display lives above the enemy (consistent for all types)
            this.ctx.fillStyle = "#FFF";
            this.ctx.strokeStyle = "#000"; // Black outline for visibility
            this.ctx.lineWidth = 1;
            this.ctx.font = `bold ${height / 3}px Arial`;
            this.ctx.textAlign = "center";
            this.ctx.textBaseline = "bottom";
            const livesText = enemy.lives.toString();
            this.ctx.strokeText(livesText, centerX, centerY - height + 5);
            this.ctx.fillText(livesText, centerX, centerY - height + 5);

            // Show damage effect if invulnerable
            if (enemy.invulnerable) {
                this.ctx.fillStyle = "rgba(255, 255, 255, 0.5)";
                this.ctx.fillRect(renderX, renderY, width, height);
            }
        }
    }

    private renderPlayers(gameState: GameState, currentPlayerId: string | null, offsetDiffX: number, offsetDiffY: number): void {
        if (!gameState.players) return;

        for (const playerId in gameState.players) {
            const player = gameState.players[playerId];
            
            // Get dimensions from entitiesInfo
            const playerUnitInfo = this.entitiesInfo.player_units[player.unit_type];
            const width = playerUnitInfo?.width || this.cellSize;
            const height = playerUnitInfo?.height || this.cellSize;

            // Определяем позицию отрисовки игрока
            let renderX: number;
            let renderY: number;
            
            // Для всех игроков используем их реальные координаты относительно смещения карты
            renderX = this.getRelativeX(player.x) + offsetDiffX;
            renderY = this.getRelativeY(player.y) + offsetDiffY;

            // Draw player
            // Use calculated width and height
            // Draw player body
            this.ctx.fillStyle = player.color;
            this.ctx.beginPath();
            this.ctx.arc(
                renderX + width / 2,
                renderY + height / 2,
                width / 2,
                0,
                Math.PI * 2
            );
            this.ctx.fill();

            // Add details to the player
            // Eyes
            this.ctx.fillStyle = "white";
            this.ctx.beginPath();
            this.ctx.arc(
                renderX + width * 0.3,
                renderY + height * 0.4,
                width * 0.15,
                0,
                Math.PI * 2
            );
            this.ctx.arc(
                renderX + width * 0.7,
                renderY + height * 0.4,
                width * 0.15,
                0,
                Math.PI * 2
            );
            this.ctx.fill();

            // Pupils
            this.ctx.fillStyle = "black";
            this.ctx.beginPath();
            this.ctx.arc(
                renderX + width * 0.35,
                renderY + height * 0.4,
                width * 0.05,
                0,
                Math.PI * 2
            );
            this.ctx.arc(
                renderX + width * 0.75,
                renderY + height * 0.4,
                width * 0.05,
                0,
                Math.PI * 2
            );
            this.ctx.fill();

            // Mouth
            this.ctx.strokeStyle = "black";
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(
                renderX + width / 2,
                renderY + height / 2,
                width * 0.25,
                0.25 * Math.PI,
                0.75 * Math.PI
            );
            this.ctx.stroke();

            // Draw highlight for current player
            if (playerId === currentPlayerId) {
                this.ctx.strokeStyle = "yellow";
                this.ctx.lineWidth = 4;
                this.ctx.strokeRect(
                    renderX - 5,
                    renderY - 5,
                    width + 10,
                    height + 10
                );
            }

            // Show invulnerability effect
            if (player.invulnerable) {
                const time = performance.now() / 1000;
                const alpha = 0.3 + Math.sin(time * 10) * 0.2;

                this.ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
                this.ctx.beginPath();
                this.ctx.arc(
                    renderX + width / 2,
                    renderY + height / 2,
                    width / 2,
                    0,
                    Math.PI * 2
                );
                this.ctx.fill();
            }

            // Draw player lives
            for (let i = 0; i < player.lives; i++) {
                this.ctx.fillStyle = "red";
                this.ctx.beginPath();
                this.ctx.arc(
                    renderX + 10 + i * 15,
                    renderY - 10,
                    5,
                    0,
                    Math.PI * 2
                );
                this.ctx.fill();
            }
        }
    }
    
    // Получить относительную координату X для отображения на экране
    private getRelativeX(worldX: number): number {
        return worldX - this.currentMapOffset.x;
    }

    // Получить относительную координату Y для отображения на экране
    private getRelativeY(worldY: number): number {
        return worldY - this.currentMapOffset.y;
    }

    // Проверить, находится ли объект в видимой области
    private isObjectVisible(x: number, y: number, width: number, height: number): boolean {
        const relX = this.getRelativeX(x);
        const relY = this.getRelativeY(y);

        return (
            relX + width >= 0 &&
            relY + height >= 0 &&
            relX <= this.viewWidth &&
            relY <= this.viewHeight
        );
    }

    // Рендерим обратный таймер в верхней части экрана в формате MM:SS
    private renderTimer(gameState: GameState): void {
        if (gameState.time_remaining == null || gameState.time_remaining <= 0) {
            return;
        }

        const totalSeconds: number = Math.ceil(gameState.time_remaining);
        const minutes: number = Math.floor(totalSeconds / 60);
        const seconds: number = totalSeconds % 60;
        const timerText: string = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        // Фон под таймером
        const textWidth: number = 120;
        const textHeight: number = 40;
        const x: number = (this.canvas.width - textWidth) / 2;
        const y: number = 10;

        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        this.ctx.beginPath();
        this.ctx.roundRect(x, y, textWidth, textHeight, 8);
        this.ctx.fill();

        // Текст таймера
        this.ctx.fillStyle = totalSeconds <= 30 ? '#ff4444' : '#ffffff';
        this.ctx.font = 'bold 24px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(timerText, this.canvas.width / 2, y + textHeight / 2);
    }

    // Рендерим отладочную информацию
    private renderDebugInfo(gameState: GameState, currentPlayerId: string | null, offsetDiffX: number, offsetDiffY: number): void {
        if (!currentPlayerId || !gameState.players[currentPlayerId]) return;

        const player = gameState.players[currentPlayerId];

        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(10, 10, 300, 140);

        this.ctx.fillStyle = 'white';
        this.ctx.font = '12px monospace';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'top';

        const gridX = Math.floor(player.x / this.cellSize);
        const gridY = Math.floor(player.y / this.cellSize);

        this.ctx.fillText(`Игрок [${currentPlayerId}]:`, 20, 20);
        this.ctx.fillText(`Позиция: ${Math.round(player.x)}, ${Math.round(player.y)}`, 20, 40);
        this.ctx.fillText(`Ячейка: ${gridX}, ${gridY}`, 20, 60);
        this.ctx.fillText(`Смещение карты: ${Math.round(this.currentMapOffset.x)}, ${Math.round(this.currentMapOffset.y)}`, 20, 80);
        this.ctx.fillText(`Целевое смещение: ${Math.round(this.targetMapOffset.x)}, ${Math.round(this.targetMapOffset.y)}`, 20, 100);
        this.ctx.fillText(`Разница смещений: ${Math.round(offsetDiffX)}, ${Math.round(offsetDiffY)}`, 20, 120);

        // Отображаем границы мёртвой зоны
        const viewCenterX = this.viewWidth / 2;
        const viewCenterY = this.viewHeight / 2;

        this.ctx.strokeStyle = 'rgba(255, 255, 0, 0.3)';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(
            viewCenterX - this.deadZoneSize.width / 2,
            viewCenterY - this.deadZoneSize.height / 2,
            this.deadZoneSize.width,
            this.deadZoneSize.height
        );
    }

    // Рендерим сообщение об ошибке
    private renderErrorMessage(message: string): void {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = 'red';
        this.ctx.font = '24px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(message, this.canvas.width / 2, this.canvas.height / 2);

        logger.error('Ошибка рендеринга', {
            message,
            canvasWidth: this.canvas.width,
            canvasHeight: this.canvas.height
        });
    }

    private darkenColor(color: string, factor: number): string {
        // Simple color darkening function
        const hex = color.replace("#", "");
        let r = parseInt(hex.substr(0, 2), 16);
        let g = parseInt(hex.substr(2, 2), 16);
        let b = parseInt(hex.substr(4, 2), 16);

        r = Math.floor(r * factor);
        g = Math.floor(g * factor);
        b = Math.floor(b * factor);

        r = Math.min(255, Math.max(0, r));
        g = Math.min(255, Math.max(0, g));
        b = Math.min(255, Math.max(0, b));

        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
}
