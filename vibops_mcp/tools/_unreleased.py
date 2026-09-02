"""
Unreleased VM actions — NOT registered in server.py.

These functions are staged for future releases. They are isolated here to:
  1. Prevent accidental registration in the MCP tool catalog
  2. Keep the main actions.py clean (only registered tools)
  3. Make review explicit when promoting tools to production

To promote a tool: move its function to actions.py, register it in server.py,
and add it to EXPECTED_TOOLS in test_server.py.
"""
from vibops_mcp.tools.actions import _run_job_sync


async def proxmox_resize_vm(vmid: int, node: str, cores: int | None = None, memory: int | None = None, disk_size: str | None = None, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Resize a Proxmox VM (CPU cores, memory MB, or disk). VM may need reboot."""
    payload: dict = {"vmid": vmid, "node": node, "confirmed": confirmed}
    if cores is not None: payload["cores"] = cores
    if memory is not None: payload["memory"] = memory
    if disk_size is not None: payload["disk_size"] = disk_size
    return await _run_job_sync("proxmox_resize_vm", payload, gateway_id=gateway_id)


async def proxmox_clone_vm(vmid: int, node: str, new_name: str, target_node: str | None = None, full_clone: bool = False, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Clone a Proxmox VM."""
    payload: dict = {"vmid": vmid, "node": node, "new_name": new_name, "full_clone": full_clone, "confirmed": confirmed}
    if target_node: payload["target_node"] = target_node
    return await _run_job_sync("proxmox_clone_vm", payload, gateway_id=gateway_id)


async def proxmox_list_snapshots(vmid: int, node: str, gateway_id: str | None = None) -> dict:
    """List all snapshots for a Proxmox VM."""
    return await _run_job_sync("proxmox_list_snapshots", {"vmid": vmid, "node": node}, gateway_id=gateway_id)


async def proxmox_restore_snapshot(vmid: int, node: str, snapname: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Restore a Proxmox VM to a previous snapshot. Current state will be lost."""
    return await _run_job_sync("proxmox_restore_snapshot", {"vmid": vmid, "node": node, "snapname": snapname, "confirmed": confirmed}, gateway_id=gateway_id)


async def proxmox_delete_snapshot(vmid: int, node: str, snapname: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Delete a snapshot from a Proxmox VM."""
    return await _run_job_sync("proxmox_delete_snapshot", {"vmid": vmid, "node": node, "snapname": snapname, "confirmed": confirmed}, gateway_id=gateway_id)


# ── XO — extended VM actions ────────────────────────────────────────────────

async def xo_delete_vm(vm_id: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Permanently delete an XCP-ng VM via Xen Orchestra."""
    return await _run_job_sync("xo_delete_vm", {"vm_id": vm_id, "confirmed": confirmed}, gateway_id=gateway_id)


async def xo_resize_vm(vm_id: str, cpus: int | None = None, memory: int | None = None, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Resize an XCP-ng VM (vCPUs or memory bytes)."""
    payload: dict = {"vm_id": vm_id, "confirmed": confirmed}
    if cpus is not None: payload["cpus"] = cpus
    if memory is not None: payload["memory"] = memory
    return await _run_job_sync("xo_resize_vm", payload, gateway_id=gateway_id)


async def xo_clone_vm(vm_id: str, new_name: str, full_clone: bool = False, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Clone an XCP-ng VM."""
    return await _run_job_sync("xo_clone_vm", {"vm_id": vm_id, "new_name": new_name, "full_clone": full_clone, "confirmed": confirmed}, gateway_id=gateway_id)


async def xo_list_snapshots(vm_id: str, gateway_id: str | None = None) -> dict:
    """List all snapshots for an XCP-ng VM."""
    return await _run_job_sync("xo_list_snapshots", {"vm_id": vm_id}, gateway_id=gateway_id)


async def xo_restore_snapshot(vm_id: str, snapshot_id: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Restore an XCP-ng VM to a previous snapshot."""
    return await _run_job_sync("xo_restore_snapshot", {"vm_id": vm_id, "snapshot_id": snapshot_id, "confirmed": confirmed}, gateway_id=gateway_id)


async def xo_delete_snapshot(vm_id: str, snapshot_id: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Delete a snapshot from an XCP-ng VM."""
    return await _run_job_sync("xo_delete_snapshot", {"vm_id": vm_id, "snapshot_id": snapshot_id, "confirmed": confirmed}, gateway_id=gateway_id)


# ── vSphere — extended VM actions ────────────────────────────────────────────

async def vsphere_delete_vm(name: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Permanently delete a vSphere VM."""
    return await _run_job_sync("vsphere_delete_vm", {"name": name, "confirmed": confirmed}, gateway_id=gateway_id)


async def vsphere_resize_vm(name: str, num_cpus: int | None = None, memory_mb: int | None = None, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Resize a vSphere VM (vCPUs or memory). VM must be powered off."""
    payload: dict = {"name": name, "confirmed": confirmed}
    if num_cpus is not None: payload["num_cpus"] = num_cpus
    if memory_mb is not None: payload["memory_mb"] = memory_mb
    return await _run_job_sync("vsphere_resize_vm", payload, gateway_id=gateway_id)


async def vsphere_clone_vm(name: str, clone_name: str, datacenter: str | None = None, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Clone a vSphere VM."""
    payload: dict = {"name": name, "clone_name": clone_name, "confirmed": confirmed}
    if datacenter: payload["datacenter"] = datacenter
    return await _run_job_sync("vsphere_clone_vm", payload, gateway_id=gateway_id)


async def vsphere_list_snapshots(name: str, gateway_id: str | None = None) -> dict:
    """List all snapshots for a vSphere VM."""
    return await _run_job_sync("vsphere_list_snapshots", {"name": name}, gateway_id=gateway_id)


async def vsphere_restore_snapshot(name: str, snapshot_name: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Restore a vSphere VM to a previous snapshot."""
    return await _run_job_sync("vsphere_restore_snapshot", {"name": name, "snapshot_name": snapshot_name, "confirmed": confirmed}, gateway_id=gateway_id)


async def vsphere_delete_snapshot(name: str, snapshot_name: str, confirmed: bool = False, gateway_id: str | None = None) -> dict:
    """Delete a snapshot from a vSphere VM."""
    return await _run_job_sync("vsphere_delete_snapshot", {"name": name, "snapshot_name": snapshot_name, "confirmed": confirmed}, gateway_id=gateway_id)


# ── Outscale (OAPI) — VM lifecycle ──────────────────────────────────────────

async def outscale_list_vms(gpu_only: bool = False, region: str | None = None, gateway_id: str | None = None) -> dict:
    """List virtual machines on Outscale. Set gpu_only=True to filter VMs with Flexible GPUs."""
    payload: dict = {}
    if gpu_only: payload["gpu_only"] = True
    if region: payload["region"] = region
    return await _run_job_sync("outscale_list_vms", payload, gateway_id=gateway_id)


async def outscale_get_vm(vm_id: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Get detailed info about a specific Outscale VM."""
    payload: dict = {"vm_id": vm_id}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_get_vm", payload, gateway_id=gateway_id)


async def outscale_start_vm(vm_id: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Start an Outscale VM."""
    payload: dict = {"vm_id": vm_id}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_start_vm", payload, gateway_id=gateway_id)


async def outscale_stop_vm(vm_id: str, force: bool = False, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Stop an Outscale VM. Set force=True for immediate hard power-off."""
    payload: dict = {"vm_id": vm_id, "force": force}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_stop_vm", payload, gateway_id=gateway_id)


async def outscale_reboot_vm(vm_id: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Reboot an Outscale VM."""
    payload: dict = {"vm_id": vm_id}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_reboot_vm", payload, gateway_id=gateway_id)


async def outscale_create_vm(image_id: str, vm_type: str, subregion: str | None = None, keypair_name: str | None = None, security_group_ids: list[str] | None = None, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Create a new Outscale VM."""
    payload: dict = {"image_id": image_id, "vm_type": vm_type}
    if subregion: payload["subregion"] = subregion
    if keypair_name: payload["keypair_name"] = keypair_name
    if security_group_ids: payload["security_group_ids"] = security_group_ids
    if region: payload["region"] = region
    return await _run_job_sync("outscale_create_vm", payload, gateway_id=gateway_id)


async def outscale_delete_vm(vm_id: str, confirmed: bool = False, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Permanently delete an Outscale VM. Set confirmed=True after user approval."""
    payload: dict = {"vm_id": vm_id, "confirmed": confirmed}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_delete_vm", payload, gateway_id=gateway_id)


async def outscale_resize_vm(vm_id: str, vm_type: str, confirmed: bool = False, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Resize an Outscale VM (change instance type). VM must be stopped."""
    payload: dict = {"vm_id": vm_id, "vm_type": vm_type, "confirmed": confirmed}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_resize_vm", payload, gateway_id=gateway_id)


# ── Outscale — Flexible GPU ─────────────────────────────────────────────────

async def outscale_list_flexible_gpus(gpu_model: str | None = None, region: str | None = None, gateway_id: str | None = None) -> dict:
    """List Flexible GPU attachments in the Outscale account."""
    payload: dict = {}
    if gpu_model: payload["gpu_model"] = gpu_model
    if region: payload["region"] = region
    return await _run_job_sync("outscale_list_flexible_gpus", payload, gateway_id=gateway_id)


async def outscale_create_flexible_gpu(model_name: str, subregion: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Allocate a new Flexible GPU."""
    payload: dict = {"model_name": model_name, "subregion": subregion}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_create_flexible_gpu", payload, gateway_id=gateway_id)


async def outscale_delete_flexible_gpu(flexible_gpu_id: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Release a Flexible GPU."""
    payload: dict = {"flexible_gpu_id": flexible_gpu_id}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_delete_flexible_gpu", payload, gateway_id=gateway_id)


async def outscale_link_flexible_gpu(flexible_gpu_id: str, vm_id: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Attach a Flexible GPU to a VM."""
    payload: dict = {"flexible_gpu_id": flexible_gpu_id, "vm_id": vm_id}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_link_flexible_gpu", payload, gateway_id=gateway_id)


async def outscale_unlink_flexible_gpu(flexible_gpu_id: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Detach a Flexible GPU from a VM."""
    payload: dict = {"flexible_gpu_id": flexible_gpu_id}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_unlink_flexible_gpu", payload, gateway_id=gateway_id)


# ── Outscale — Snapshots ────────────────────────────────────────────────────

async def outscale_list_snapshots(region: str | None = None, gateway_id: str | None = None) -> dict:
    """List BSU snapshots on Outscale."""
    payload: dict = {}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_list_snapshots", payload, gateway_id=gateway_id)


async def outscale_create_snapshot(volume_id: str, description: str | None = None, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Create a snapshot of a BSU volume."""
    payload: dict = {"volume_id": volume_id}
    if description: payload["description"] = description
    if region: payload["region"] = region
    return await _run_job_sync("outscale_create_snapshot", payload, gateway_id=gateway_id)


async def outscale_delete_snapshot(snapshot_id: str, confirmed: bool = False, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Delete a BSU snapshot."""
    payload: dict = {"snapshot_id": snapshot_id, "confirmed": confirmed}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_delete_snapshot", payload, gateway_id=gateway_id)


# ── Outscale — Billing ──────────────────────────────────────────────────────

async def outscale_get_consumption(from_date: str, to_date: str, region: str | None = None, gateway_id: str | None = None) -> dict:
    """Get billing consumption for the Outscale account."""
    payload: dict = {"from_date": from_date, "to_date": to_date}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_get_consumption", payload, gateway_id=gateway_id)


async def outscale_get_quota(region: str | None = None, gateway_id: str | None = None) -> dict:
    """Get resource quotas for the Outscale account."""
    payload: dict = {}
    if region: payload["region"] = region
    return await _run_job_sync("outscale_get_quota", payload, gateway_id=gateway_id)
