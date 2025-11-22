import asyncio
import websockets
import os

# Conjuntos para guardar los clientes conectados
laptop_clients = set()
pc_clients = set()

async def handler(websocket, path):
    print(f"Nueva conexión desde {websocket.remote_address}")
    role = None
    
    try:
        # Esperamos el primer mensaje que nos diga quién es ("laptop" o "pc")
        role = await websocket.recv()
        
        if role == "laptop":
            laptop_clients.add(websocket)
            print("Laptop conectada (Emisor)")
        elif role == "pc":
            pc_clients.add(websocket)
            print("PC conectada (Visor)")
        else:
            # Si no se identifica, cerramos
            await websocket.close()
            return

        # Bucle principal de retransmisión
        async for message in websocket:
            if role == "laptop":
                # Si el mensaje viene de la laptop, se lo mandamos a TODAS las PCs conectadas
                if not pc_clients:
                    pass # No hay nadie viendo, solo ignoramos
                else:
                    # Retransmitir a todos los visores
                    # Usamos un conjunto para eliminar clientes desconectados durante el envío
                    disconnected_pcs = set()
                    for pc in pc_clients:
                        try:
                            await pc.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_pcs.add(pc)
                    
                    # Limpiar clientes muertos
                    pc_clients.difference_update(disconnected_pcs)

    except websockets.exceptions.ConnectionClosed:
        print(f"Conexión cerrada: {role}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Limpieza final al desconectarse
        if role == "laptop" and websocket in laptop_clients:
            laptop_clients.remove(websocket)
        elif role == "pc" and websocket in pc_clients:
            pc_clients.remove(websocket)

async def main():
    # OBTENER EL PUERTO DE RENDER (CRÍTICO)
    # Si no existe la variable PORT (ej. localmente), usa 8765
    port = int(os.environ.get("PORT", 8765))
    print(f"Iniciando servidor en puerto {port}...")
    
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # Correr para siempre

if __name__ == "__main__":
    asyncio.run(main())
