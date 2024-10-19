import asyncio

from utils import Odrive, find_odrvs_async


async def calibrate(odrv: Odrive):
    print(f"Calibrating {odrv.section} odrive...")
    odrv.check_errors()  # Checking errors before starting
    # set configurations then reboot if needed
    if odrv.config.set_break_resistor(0.5) | odrv.set_configs():
        print(f"need to reset the system for new configurations")
        await odrv.reboot(save_config=True)
    await odrv.calibrate()
    if odrv.has_errors():
        print(f"{odrv.section} odrive calibration fail!")
        odrv.check_errors()  # Checking errors at the end
        return

    final_data: list = []
    
    print(f"{odrv.section} odrive calibration completed. Test run...")
    for speed in [2, 5, 10]:
        data = await odrv.test_run(speed, speed * 0.5 + 1)
        final_data.append(data)
    if odrv.has_errors():
        print(f"{odrv.section} test run fail!")
        return

    print(f"{odrv.section} test run completed. Save configuration profile...")
    await odrv.reboot(save_config=True)


async def main():
    odrvs: list[Odrive] = await find_odrvs_async()
    print("Running Calibration ...")
    for odrv in odrvs:
        await calibrate(odrv)


if __name__ == "__main__":
    asyncio.run(main())
